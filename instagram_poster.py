"""
instagram_poster.py — Uploads generated images to Instagram via instagrapi.
Posts all constituency images as a carousel (album) post.
Instagram limit is 10 images per carousel, so 24 images = 3 separate posts.
"""

from instagrapi import Client
from datetime import datetime
import os


class InstagramPoster:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.client = Client()
        self._logged_in = False

    def login(self) -> bool:
        """Log in to Instagram. Returns True on success."""
        try:
            session_file = f"ig_session_{self.username}.json"
            if os.path.exists(session_file):
                self.client.load_settings(session_file)
                self.client.login(self.username, self.password)
            else:
                self.client.login(self.username, self.password)

            # Always re-save session so refreshed tokens are persisted
            self.client.dump_settings(session_file)

            self._logged_in = True
            print(f"[Instagram] Logged in as @{self.username}")
            return True
        except Exception as e:
            print(f"[Instagram] Login failed: {e}")
            self._logged_in = False
            return False

    def post_image(self, image_path: str, caption: str | None = None) -> bool:
        """Upload a single image post."""
        if not self._logged_in:
            print("[Instagram] Not logged in. Call login() first.")
            return False

        if not os.path.exists(image_path):
            print(f"[Instagram] File not found: {image_path}")
            return False

        if caption is None:
            caption = self._build_caption()

        try:
            media = self.client.photo_upload(image_path, caption)
            # Re-save session after every successful API call
            self.client.dump_settings(f"ig_session_{self.username}.json")
            print(f"[Instagram] Posted single image. Media ID: {media.pk}")
            return True
        except Exception as e:
            print(f"[Instagram] Upload failed: {e}")
            return False

    def post_carousel(self, image_paths: list[str], caption: str | None = None) -> bool:
        """
        Upload multiple images as carousel post(s).
        Instagram allows up to 10 images per carousel.
        If more than 10 images are provided, they are split into batches of 10
        and posted as multiple carousels — a clear warning is printed.
        """
        if not self._logged_in:
            print("[Instagram] Not logged in. Call login() first.")
            return False

        valid_paths = [p for p in image_paths if os.path.exists(p)]
        if not valid_paths:
            print("[Instagram] No valid image files found.")
            return False

        if len(valid_paths) > 10:
            total_batches = (len(valid_paths) + 9) // 10
            print(
                f"[Instagram] WARNING: {len(valid_paths)} images exceed Instagram's "
                f"10-image carousel limit. This will create {total_batches} separate "
                f"posts rather than one. Consider reducing to <= 10 constituencies "
                f"per run to keep it as a single post."
            )
            return self._post_carousel_batches(valid_paths, caption)

        if caption is None:
            caption = self._build_caption(len(valid_paths))

        try:
            media = self.client.album_upload(valid_paths, caption)
            self.client.dump_settings(f"ig_session_{self.username}.json")
            print(f"[Instagram] Carousel posted. {len(valid_paths)} images, Media ID: {media.pk}")
            return True
        except Exception as e:
            print(f"[Instagram] Carousel upload failed: {e}")
            print("[Instagram] Trying fallback: single image post ...")
            return self.post_image(valid_paths[0], caption)

    def _post_carousel_batches(self, image_paths: list[str], caption: str | None) -> bool:
        """Post images in batches of 10."""
        total_batches = (len(image_paths) + 9) // 10
        success = 0

        for i in range(0, len(image_paths), 10):
            batch     = image_paths[i:i + 10]
            batch_num = (i // 10) + 1

            batch_caption = caption or self._build_caption(len(batch))
            if total_batches > 1:
                batch_caption = f"[{batch_num}/{total_batches}] {batch_caption}"

            try:
                media = self.client.album_upload(batch, batch_caption)
                self.client.dump_settings(f"ig_session_{self.username}.json")
                print(
                    f"[Instagram] Batch {batch_num}/{total_batches} posted. "
                    f"{len(batch)} images, Media ID: {media.pk}"
                )
                success += 1
            except Exception as e:
                print(f"[Instagram] Batch {batch_num} failed: {e}")

        return success > 0

    def post_multiple(self, image_paths: list[str]) -> bool:
        """
        Main posting method. Posts all images as carousel(s).
        Returns True on success, False on failure.
        """
        if not image_paths:
            return False

        caption = self._build_caption(len(image_paths))

        if len(image_paths) == 1:
            return self.post_image(image_paths[0], caption)
        else:
            return self.post_carousel(image_paths, caption)

    def _build_caption(self, num_constituencies: int = 0) -> str:
        """Build Instagram caption with timestamp and hashtags."""
        now = datetime.now().strftime("%d %b %Y, %I:%M %p")
        lines = ["Nepal Election 2082 - Live Update"]

        # Only include constituency count line when count is meaningful
        if num_constituencies > 0:
            lines.append(f"{num_constituencies} Constituencies")

        lines.extend([
            f"Updated: {now}",
            "",
            "Swipe to see all constituency results",
            "",
            "Source: ekantipur.com",
            "",
            "#NepalElection2082 #Nepal #Election2082 "
            "#NepaliPolitics #VoteNepal #Nepal2082",
        ])
        return "\n".join(lines)

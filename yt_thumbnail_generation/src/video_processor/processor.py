"""Video processor functions using yt_dlp"""
# pylint: disable=too-many-branches
import os
import tempfile
import cv2
import yt_dlp
import numpy as np
import streamlit as st

from utils.utility import clean_title, strip_escape_seqs

def update_download_progress(d):
    """Callback hook for updating download progress"""
    if d['status'] == 'downloading':
        download_percent = strip_escape_seqs(d['_percent_str'])
        download_progress = float(download_percent.replace('%', '')) / 100
        st.session_state.video_processor_progress.progress(download_progress,
                                                           text="Downloading video...")

def generate_snapshots(video_path, num_snapshots=5, output_dir = "snapshots"):
    """Generate snapshots for the video"""
    print(f"\n--- Taking Snapshots for: {video_path} ---")
    snapshots_filepath = []

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created parent directory for snapshots: {output_dir}")

    video_name = os.path.splitext(os.path.basename(video_path))[0]
    video_snapshot_dir = os.path.join(output_dir, video_name)

    if not os.path.exists(video_snapshot_dir):
        os.makedirs(video_snapshot_dir)
        print(f"Created directory for video snapshots: {video_snapshot_dir}")

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path} with OpenCV.")
        if os.path.exists(video_path): # Clean up downloaded file
            try:
                os.remove(video_path)
                print(f"Cleaned up temporary video file: {video_path}")
            except OSError as e:
                print(f"Error deleting temporary file {video_path}: {e}")
        return None

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")

    frame_indices = np.linspace(0, total_frames - 1, num=num_snapshots, dtype=int)

    for i, frame_id in enumerate(frame_indices):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if ret:
            snapshot_filename = os.path.join(video_snapshot_dir, f"snapshot_{i+1}.png")
            cv2.imwrite(snapshot_filename, frame)
            print(f"Saved snapshot: {snapshot_filename} (from frame {frame_id})")
            snapshots_filepath.append(snapshot_filename)
        else:
            print(f"Error reading frame {frame_id} for snapshot {i+1}.")

    cap.release()
    print("\nSnapshot process complete.")

    # Clean up the downloaded video file from the temp directory
    if os.path.exists(video_path):
        try:
            os.remove(video_path)
            print(f"Cleaned up temporary video file: {video_path}")
        except OSError as e:
            print(f"Error deleting temporary file {video_path}: {e}")

    return snapshots_filepath

def get_video_data(url, num_snaps = 5, min_duration = 120, download_dir = "downloads"):
    """Process youtube video and get required data"""
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        if 'title' in info_dict and isinstance(info_dict['title'], str):
            title = clean_title(info_dict['title'])

        if 'duration' in info_dict and isinstance(info_dict['duration'], int):
            video_duration = info_dict['duration']

            if video_duration < min_duration:
                print("Shorter video, using mp4 file directly")

                if not os.path.exists(download_dir):
                    os.makedirs(download_dir)
                    print(f"Created downloads directory: {download_dir}")

                file_path = os.path.abspath(f"downloads/{title}.mp4")
                ydl_opts = {
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': file_path,
                    'progress_hooks': [update_download_progress],
                    'quiet': False,
                    'no_warnings': True,
                    'noplaylist': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                        ydl_download.download([url])
                    if 'video_processor_progress' in st.session_state:
                        st.session_state.video_processor_progress.empty()
                        del st.session_state.video_processor_progress
                    return info_dict, file_path
                except yt_dlp.utils.DownloadError as e:
                    print(f"Error during download or info extraction: {e}")
                    raise ValueError(e) from e
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    raise ValueError(e) from e
            elif min_duration < video_duration < 1800:
                print("Longer video, downloading mp4 file and generating snapshots")

                file_path = os.path.join(tempfile.gettempdir(), f"{title}.mp4")
                ydl_opts = {
                    # TODO: Change format to low quality(480p) for longer videos
                    # or even less and ignore audio
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                    'outtmpl': file_path,
                    'progress_hooks': [update_download_progress],
                    'quiet': False,
                    'no_warnings': True,
                    'noplaylist': True,
                }

                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_download:
                        ydl_download.download([url])

                    if 'video_processor_progress' in st.session_state:
                        st.session_state.video_processor_progress.empty()
                        del st.session_state.video_processor_progress

                    media_path = generate_snapshots(file_path, num_snapshots=num_snaps)

                    return info_dict, media_path
                except yt_dlp.utils.DownloadError as e:
                    print(f"Error during download or info extraction: {e}")
                    raise ValueError(e) from e
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    raise ValueError(e) from e
            else:
                print("Video is longer than 1/2 hour, skipping")
                return None, None
        else:
            print("Video duration not found, skipping")
            return None, None

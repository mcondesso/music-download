"""Module for handling youtube download"""
import os

from moviepy.video.io.VideoFileClip import VideoFileClip
from pytubefix import YouTube

from src.file_metadata import FILE_EXTENSION_MP3, FILE_EXTENSION_MP4

NUM_RETRIES = 5


def get_audio_from_youtube(youtube_url: str, output_dir: str, filename: str) -> str:
    """This function downloads a song from youtube.

    In a first attempt, we download the video and then extract the audio, as this
    way proved to be more reliable.
    If that fails, we attempt to download the audio stream directly from youtube.
    """
    mp4_filepath = _download_mp4_video_from_youtube(youtube_url, output_dir, filename)

    if _is_mp4_file_audio_only(mp4_filepath):
        return mp4_filepath

    # If mp4 file contains video, we have to extract the audio track
    video_processing_failed = False
    try:
        # Extract the audio file from the previously downloaded .mp4 file.
        audio_filepath = _extract_audio_from_mp4_video(mp4_filepath)
    except KeyError as error:
        print(f"Error extracting mp3 from {mp4_filepath}: {error}")
        video_processing_failed = True
    finally:
        os.remove(mp4_filepath)

    # In case of error, download the audio directly using the only_audio=True flag. This is not
    # the default approach because this can lead to corrupted downloaded files, so we only use
    # it as a fallback.
    if video_processing_failed:
        audio_filepath = _download_mp4_audio_from_youtube(
            youtube_url, output_dir, filename
        )

    return audio_filepath


def _download_mp4_video_from_youtube(
    youtube_url: str, output_dir: str, filename: str
) -> str:
    """This function downloads an mp4 video stream from youtube."""
    # Ensure the filename contains the correct extension
    if not filename.endswith(FILE_EXTENSION_MP4):
        filename += FILE_EXTENSION_MP4

    print(f"\nDownloading '{filename.rstrip(FILE_EXTENSION_MP4)}'")

    yt = YouTube(youtube_url)

    # Get stream with video in mp4 format, order by Average Bit Rate and take highest bit rate
    video = yt.streams.filter(subtype="mp4").order_by("abr").last()
    video.download(output_path=output_dir, max_retries=NUM_RETRIES, filename=filename)

    return os.path.join(output_dir, filename)


def _download_mp4_audio_from_youtube(
    youtube_url: str, output_dir: str, filename: str
) -> str:
    """This function downloads an mp4 audio stream from youtube."""
    # Ensure the filename contains the correct extension
    if not filename.endswith(FILE_EXTENSION_MP4):
        filename += FILE_EXTENSION_MP4

    print(f"\nDownloading '{filename.rstrip(FILE_EXTENSION_MP4)}'")

    yt = YouTube(youtube_url)

    # Get stream with only audio in mp4 format, order by Average Bit Rate and take highest bit rate
    video = yt.streams.filter(only_audio=True, subtype="mp4").order_by("abr").last()

    video.download(output_path=output_dir, max_retries=NUM_RETRIES, filename=filename)

    return os.path.join(output_dir, filename)


def _extract_audio_from_mp4_video(video_filepath: str) -> str:
    """This function extracts the audio of an mp4 video."""
    if not video_filepath.endswith(FILE_EXTENSION_MP4):
        raise ValueError(f"Input video is not in mp4 format: {video_filepath}")

    output_filename = video_filepath.replace(FILE_EXTENSION_MP4, FILE_EXTENSION_MP3)

    video_clip = VideoFileClip(video_filepath)
    audio_clip = video_clip.audio
    audio_clip.write_audiofile(output_filename, codec="mp3")
    video_clip.close()

    return output_filename


def _is_mp4_file_audio_only(mp4_filepath: str) -> bool:
    """This function checks whether an mp4 file is audio only."""
    try:
        VideoFileClip(mp4_filepath)
    except KeyError as error:
        if "video_fps" in str(error):
            # Error thrown when mp4 file is already audio only
            return True
        else:
            # Reraise unknown KeyError
            raise
    return False

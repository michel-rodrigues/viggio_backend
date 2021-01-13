import asyncio
import os
import subprocess
import shutil
import tempfile
from contextlib import contextmanager
from django.conf import settings
from django.core.files.storage import default_storage


TRANSCODED_VIDEO_GENERIC_NAME = 'transcoded_video'


class TranscodeError(Exception):
    pass


@contextmanager
def tempfilename(extension):
    dir = tempfile.mkdtemp()
    yield os.path.join(dir, 'tempoutput' + extension)
    shutil.rmtree(dir)


async def convert(input_file, output_file):
    # TODO: figure out a way to dinamicaly get water mark. Using open() was causing
    # tempfilename issue, so hardcode the path was the easy way to solve it
    command = (
        'ffmpeg '
        f'-i {input_file} '
        f'-i /usr/src/app/transcoder/media/logo-white.png '
        '-filter_complex '
        '"[1][0]scale2ref=h=ow/mdar:w=iw/3[#A logo][viggio];'
        '[#A logo]format=argb,colorchannelmixer=aa=0.7[#B logo transparent];'
        '[viggio][#B logo transparent]overlay=(main_w-w)-(main_w*0.005):(main_h-h)-(main_h*0.005)"'
        f' {output_file} '
        f'&& rm {input_file}'
    )
    proc = await asyncio.create_subprocess_shell(
        cmd=command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return stdout, stderr


def validate(file_path):
    command = (
        'ffmpeg',
        '-v',
        'error',
        '-i',
        f'{file_path}',
        '-map',
        '0:1',
        '-f',
        'null',
        '/dev/null',
    )
    completed_process = subprocess.run(command, stderr=subprocess.PIPE)
    if completed_process.stderr:
        raise TranscodeError(completed_process.stderr)


def transcode(video_model, extension):
    video_uploaded_url = video_model.file.url
    with tempfilename(f'.{extension}') as output_file_path:
        temp_input_file, input_file_path = tempfile.mkstemp()
        with open(temp_input_file, 'wb') as container_file:
            container_file.write(video_model.file.file.read())
            container_file.seek(0)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(convert(input_file_path, output_file_path))
        validate(output_file_path)
        with open(output_file_path, 'rb') as transcoded_video:
            video_model.file.save(
                f'{TRANSCODED_VIDEO_GENERIC_NAME}.{extension}',
                transcoded_video,
                save=True,
            )
    # Delete original file in Storage
    default_storage.delete(video_uploaded_url[len(settings.MEDIA_URL):])
    # Add "Content-Disposition: attachment" response header to trigger the download file on browser
    file = default_storage.open(video_model.file.url[len(settings.MEDIA_URL):], 'r')
    if hasattr(file, 'blob'):
        file.blob.content_disposition = "attachment"
        file.blob.patch()
    file.close()

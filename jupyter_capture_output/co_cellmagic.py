from io import BytesIO
from base64 import b64decode

from IPython.core import magic_arguments
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.display import display
from IPython.utils.capture import capture_output
from PIL import Image
from pathlib import Path
from pprint import pprint # for debugging
import re


def path_preprocessing(path):
    # print(type(path))  # for debugging
    path_pathlib = Path(path)
    if not path_pathlib.parent.exists():
        path_pathlib.parent.mkdir(exist_ok=False , parents=True)
        print(f"Note: The {path_pathlib.parent} directory was successfully created.")
    print(f"Output is saved at {path_pathlib}") # TODO: Call this later maybe?
    return path_pathlib
@magics_class
class CaptureMagic(Magics):
    
    @magic_arguments.magic_arguments() ################### TEXT
    @magic_arguments.argument(
        "--path",
        "-p",
        default=None,
        help=(
            "The path where the text will be saved to"
        ),
    )
    @cell_magic
    def capture_text(self, line, cell):
        args = magic_arguments.parse_argstring(CaptureMagic.capture_text, line)
        paths_string = args.path.strip('"').split(" ")
        paths_pathlib = [] 
        # paths_string has only one element for capture text, so this would not be necessary here.
        # It's just for convenicene, as the other capture functions have the same loop. 
        for path_str in paths_string: 
            path_pathlib = path_preprocessing(path_str)
            paths_pathlib.append(path_pathlib)

        with capture_output(stdout=True, stderr=False, display=False) as result:
            self.shell.run_cell(cell)
            message = result.stdout

        if len(message) == 0:
            raise ValueError("No standard output (stdout) found!")
        print(message)
        dest = paths_pathlib[0]
        dest.write_text(message)


    @magic_arguments.magic_arguments() ################### IMAGE
    @magic_arguments.argument(
        "--path",
        "-p",
        default=None,
        help=(
            "The path where the image will be saved to. When there is more then one image, multiple paths have to be defined"
        ),
    )
    @magic_arguments.argument(
        "--compression",
        "-c",
        default=None,
        help=(
            "Defines the amount of compression,  quality can be from 0.1 - 100 , images must be .jpg"
        ),
    )
    @cell_magic
    def capture_img(self, line, cell):
        args = magic_arguments.parse_argstring(CaptureMagic.capture_img, line)
        paths = args.path.strip('"').split(" ")
        with capture_output(stdout=False, stderr=False, display=True) as result:
            self.shell.run_cell(cell)
        for output in result.outputs:
            display(output)
            data = output.data
            if "image/png" in data:
                path = paths.pop(0)
                if not path:
                    raise ValueError("Too few paths given!")
                png_bytes = data["image/png"]
                if isinstance(png_bytes, str):
                    png_bytes = b64decode(png_bytes)
                assert isinstance(png_bytes, bytes)
                bytes_io = BytesIO(png_bytes)
                img = Image.open(bytes_io)
                if args.compression:
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(path, "JPEG", optimize=True, quality=int(args.compression))
                else:
                    img.save(path, "png")


    @magic_arguments.magic_arguments() ################### Video
    @magic_arguments.argument(
        "--path",
        "-p",
        default=None,
        help=(
            "The path where the video will be saved to. When there is more then one video, multiple paths have to be defined"
        ),
    )
    @cell_magic
    def capture_video(self, line, cell):
        args = magic_arguments.parse_argstring(CaptureMagic.capture_video, line)
        paths = args.path.strip('"').split(" ")
        with capture_output(stdout=False, stderr=False, display=True) as result:
            self.shell.run_cell(cell)
        for output in result.outputs:
            display(output)
            data = output.data
            # pprint(data) # for debugging 

            if "text/html" in data: # this is not nice, is there any better way to access IPython.core.display.Video object ?
                path = paths.pop(0)
                if not path:
                    raise ValueError("Too few paths given!")
                video_object_html_string = data["text/html"]
                # find path in e.g. '<video src="assets/DopplerTest.mp4" controls  width="300" >
                video_dir = re.findall(r'video src="(.+?)"', video_object_html_string)[0] 
                dest = Path(path)
                src = Path(video_dir)
                dest.write_bytes(src.read_bytes())


    ### The rest of this script is still very experimental and might be removed in future.         

    @magic_arguments.magic_arguments() ################### Video experiment
    @magic_arguments.argument(
        "--path",
        "-p",
        default=None,
        help=(
            "The path where the video will be saved to. When there is more then one video, multiple paths have to be defined"
        ),
    )
    @cell_magic
    def experimental_capture_video_first_last(self, line, cell):
        args = magic_arguments.parse_argstring(CaptureMagic.experimental_capture_video_first_last, line)
        paths = args.path.strip('"').split(" ")
        with capture_output(stdout=False, stderr=False, display=True) as result:
            self.shell.run_cell(cell)
        for output in result.outputs:
            display(output)
            data = output.data
            # pprint(data) # for debugging 

            if "text/html" in data: # this is not nice, is there any better way to access IPython.core.display.Video object ?
                path = paths.pop(0)
                if not path:
                    raise ValueError("Too few paths given!")
                video_object_html_string = data["text/html"]
                # find path in e.g. '<video src="assets/DopplerTest.mp4" controls  width="300" >
                video_dir = re.findall(r'video src="(.+?)"', video_object_html_string)[0] 
                dest = Path(path)
                src = Path(video_dir)
                dest.write_bytes(src.read_bytes())
                
                import os
                input = str(dest)
                output = str(input)
                output = output[:-4] # delete the ending
                print(output)
                command = f"ffmpeg -i {input} -vframes 1 {output}_start.png"
                os.system(f'echo 3 | {command} >/dev/null 2>&1') # makes sure to print output not into cell output

                command = f"ffmpeg  -sseof -3 -i {input} -update 1 -q:v 1 {output}_end.png"
                os.system(f'echo 3 | {command} >/dev/null 2>&1') # makes sure to print output not into cell output

    @magic_arguments.magic_arguments() ################### Video experiment
    @magic_arguments.argument(
        "--path",
        "-p",
        default=None,
        help=(
            "The path where the video will be saved to. When there is more then one video, multiple paths have to be defined"
        ),
    )
    @cell_magic
    def experimental_video_thumbnail(self, line, cell):
        args = magic_arguments.parse_argstring(CaptureMagic.experimental_video_thumbnail, line)
        paths = args.path.strip('"').split(" ")
        with capture_output(stdout=False, stderr=False, display=True) as result:
            self.shell.run_cell(cell)
        for output in result.outputs:
           # display(output)
            data = output.data
            # pprint(data) # for debugging 

            if "text/html" in data: # this is not nice, is there any better way to access IPython.core.display.Video object ?
                path = paths.pop(0)
                if not path:
                    raise ValueError("Too few paths given!")
                video_object_html_string = data["text/html"]
                # find path in e.g. '<video src="assets/DopplerTest.mp4" controls  width="300" >
                video_dir = re.findall(r'video src="(.+?)"', video_object_html_string)[0] 
                dest = Path(path)
                src = Path(video_dir)
                dest.write_bytes(src.read_bytes())
                
                import os
                input = str(dest)
                output = str(input)
                output = output[:-4] # delete the ending
                command = f"ffmpeg -i {input} -vframes 1 {output}_start.png"
                os.system(f'echo 3 | {command} >/dev/null 2>&1') # makes sure to print output not into cell output

                command = f"ffmpeg  -sseof -3 -i {input} -update 1 -q:v 1 {output}_end.png"
                os.system(f'echo 3 | {command} >/dev/null 2>&1') # makes sure to print output not into cell output


                import matplotlib.pyplot as plt
                fig, (ax1, ax2) = plt.subplots(1,2)

                im1 = plt.imread(f"{output}_start.png")
                ax1.imshow(im1)
                ax1.axis("off")
                ax1.set_title('First Frame')


                im2 = plt.imread(f"{output}_end.png")
                ax2.imshow(im2)
                ax2.axis("off")
                ax2.set_title('Last Frame')

import datetime
import os

def saveBlendFileBinary(binaryBlendData , customerEmail):
        # dir_path = f'CustomerData/paarthsaxena2005@gmail.com/Rendering'
        dir_path = f"CustomerData/{customerEmail}/Rendering"
        os.makedirs(dir_path , exist_ok=True)

        file_name = (datetime.datetime.now().strftime("%Y-%m-%d,%H-%M-%S"))
        sub_dir_path = f'{dir_path}/{file_name}'
        os.makedirs(sub_dir_path , exist_ok=True)

        input_file_path = f'{sub_dir_path}/InputBlendFile'
        os.makedirs(input_file_path , exist_ok=True)

        output_file_path = f'{sub_dir_path}/RenderedFiles'
        os.makedirs(output_file_path , exist_ok=True)

        renderer_images_path = f'{output_file_path}/Images'
        os.makedirs(renderer_images_path , exist_ok=True)

        renderer_videos_path = f'{output_file_path}/Video'
        os.makedirs(renderer_videos_path , exist_ok=True)

        with open(f"{input_file_path}/{str(file_name)}.blend" , "wb") as file:
            file.write(binaryBlendData)
        
        # self.currentFolder = sub_dir_path
        # self.renderedImagesFolder = renderer_images_path
        return f"{input_file_path}/{str(file_name)}" + ".blend"


blendBinary = ""
with open('./Testing/test.blend' , 'rb') as file:
    blendBinary = file.read()

customerEmail = "paarthsaxena2005@gmail.com"

path = saveBlendFileBinary(blendBinary , customerEmail)
print(path)

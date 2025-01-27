import subprocess

# Returns the Last and First Frame of a Scene in Blender
def getLastAndFirstFrame(self , blendFileName):
    script_path = "getFrameRange.py"

    result = subprocess.run(["blender", "--background", blendFileName, "--python", script_path], capture_output=True , text = True)

    self.logger.info(f"Output of the Process : {result.stdout}")

    output = result.stdout.split("\n")

    first_frame = [line.split(":")[1] for line in output if "FF" in line.split(":")[0]][0]
    last_frame = [line.split(":")[1] for line in output if "LF" in line.split(":")[0]][0]

    frameList = [last_frame, first_frame]
    return frameList


blendFileName = "CustomerData/paarthsaxena2005@gmail.com/Rendering/2025-01-27,19-51-01/InputBlendFile/2025-01-27,19-51-01.blend"
script_path = "service_SessionSupervisor/getFrameRange.py"

command = f"blender --background {blendFileName} --python {script_path}"
print(command)
print()

command = "blender --background CustomerData/paarthsaxena2005@gmail.com/Rendering/2025-01-27,19-51-01/InputBlendFile/2025-01-27,19-51-01.blend --python service_SessionSupervisor/getFrameRange.py"
print(command)
print()

result = subprocess.run([command], capture_output=True , text = True, shell=True)
print(result.stdout)

# cmd = "blender --background CustomerData/paarthsaxena2005@gmail.com/Rendering/2025-01-27,19-32-22/InputBlendFile/2025-01-27,19-32-22.blend --python Testing/getFrameRange.py"
# res = subprocess.run([cmd], capture_output=True , text = True , shell=True)
# print(res.stdout)

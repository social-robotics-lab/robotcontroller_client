import subprocess
import os.path

# Path to which OpenJTalk was installed
OPENJTALK_BINPATH = '/usr/bin'
OPENJTALK_DICPATH = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
OPENJTALK_VOICEPATH = '/usr/share/hts-voice/mei/mei_{emotion}.htsvoice'

def make_wav(text, speed=1.0, emotion='normal', output_file='__temp.wav', output_dir=os.getcwd()):
    """
    Function to make a wav file using OpenJTalk.
    args:
        speed: The speed of speech. (Default: 1.0)
        emotion: Voice emotion. You can specify 'normal', 'happy', 'bashful', 'angry', or 'sad'.
        output_file: The file name made by this function. (Default: '__temp.wav')
        output_dir: The directory of output_file. (Default: Current directory)
    """
    open_jtalk = [OPENJTALK_BINPATH + '/open_jtalk']
    mech = ['-x', OPENJTALK_DICPATH]
    htsvoice = ['-m', OPENJTALK_VOICEPATH.format(emotion=emotion)]
    speed = ['-r', str(speed)]
    outwav = ['-ow', os.path.join(output_dir, output_file)]
    cmd = open_jtalk + mech + htsvoice + speed + outwav
    c = subprocess.Popen(cmd,stdin=subprocess.PIPE)
    c.stdin.write(text.encode('utf-8'))
    c.stdin.close()
    c.wait()
    return os.path.join(output_dir, output_file)

if __name__ == '__main__':
    make_wav('こんにちは。今日はいい天気ですね。')
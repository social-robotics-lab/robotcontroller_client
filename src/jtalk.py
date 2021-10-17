import subprocess
import os.path

def make_wav(text, speed=1.0, emotion='normal', output_file='__temp.wav', output_dir=os.getcwd(), voice_name='mei',
             openjtalk_binpath='/usr/bin',
             openjtalk_dicpath='/var/lib/mecab/dic/open-jtalk/naist-jdic',
             openjtalk_voicepath='/usr/share/hts-voice/{voice_name}/{voice_name}_{emotion}.htsvoice'):
    """
    Function to make a wav file using OpenJTalk.
    args:
        speed: The speed of speech. (Default: 1.0)
        emotion: Voice emotion. You can specify 'normal', 'happy', 'bashful', 'angry', or 'sad'.
        output_file: The file name made by this function. (Default: '__temp.wav')
        output_dir: The directory of output_file. (Default: Current directory)
    """
    open_jtalk = [openjtalk_binpath + '/open_jtalk']
    mech = ['-x', openjtalk_dicpath]
    htsvoice = ['-m', openjtalk_voicepath.format(voice_name=voice_name, emotion=emotion)]
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
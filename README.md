# robotcontroller_client
Sample programs for communicating with Sota (CommU).


# Install
```
git clone https://github.com/social-robotics-lab/robotcontroller_client.git
cd robotcontroller_client
docker build -t robotcontroller_client .
```

# Run

```
docker run -it --name robotcontroller_client --mount type=bind,source="$(pwd)"/src,target=/tmp --rm robotcontroller_client /bin/bash
python sample.py --host 192.168.x.x 
```

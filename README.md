# Project Name
P2P file sharing application

## Description
allow you download files via p2p network

## Installation


```bash
# Example
git clone https://github.com/blueonline07/net-app
cd net-app
pip install -r requirements.txt
```

## Usage

```bash
# Example
python3  main.py [-h] [--torrent TORRENT] [--runserver] [--port PORT] [--download]
```
- `-h` for help
- `--torrent` specify the path to the torrent file you wnat to download
- `--runserver` serve the files so that people can find you
- `--port` specify the port you want your app listen to
- `--download` if you want to download the files
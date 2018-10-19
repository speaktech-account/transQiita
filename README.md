This application translates your articles on Qiita into English ones with googletrans, and 
upload them to Qiita automatically. 

Example:
    $ python transQiita.py  [-h] [--gist] [--tweet] [--private] [--auto] [--token TOKEN]

optional arguments:
    -h, --help     show this help message and exit
    --gist         upload translated article to gist
    --tweet        tweet about translated article
    --private      set publish format to private
    --auto         execute translation and upload automatically
    --token TOKEN  set Qiita's access token

Requirements:
    googletrans, Qiita access token(Set as Environment variable QIITA_ACCESS_TOKEN)
    
    e.g.
    $ pip install googletrans
    $ export QIITA_ACCESS_TOKEN='YOUR QIITA ACCESS TOKEN'

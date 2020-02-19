#!/bin/sh

python2 manager.py db upgrade
exec python2 main.py --host 0.0.0.0

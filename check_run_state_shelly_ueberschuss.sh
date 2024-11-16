#!/bin/bash
var=$(date)
if pgrep -af python | grep shelly_ueberschuss >/dev/null
then
  echo "$var: Ueberschuss laeuft"
else
  echo "$var: Ueberschuss laeuft NICHT -> Restart"
  nohup python3 /home/pi/shelly_ueberschuss/shelly_ueberschuss.py > /home/pi/output_shelly_ueberschuss.log &
fi


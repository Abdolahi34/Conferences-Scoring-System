#!/bin/bash
# To keep the project stable, this file must be executed every minute.


for i in {1..12};
do
/usr/bin/curl http://example.com/score/save/
sleep 4.5;
done

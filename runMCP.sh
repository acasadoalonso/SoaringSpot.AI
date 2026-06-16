
export SOARINGSPOT_COMPNAME='wgc2026'
#export SOARINGSPOT_COMPNAME='24-fai-egc'
pkill -f "python server.py --host 0.0.0.0 --port 9009 --path /soaringspot"
python server.py --host 0.0.0.0 --port 9009 --path /soaringspot >>/tmp/mcpSS.log 2>&1  &


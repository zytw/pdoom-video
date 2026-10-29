#!/bin/bash
# 用法: tools/sheet.sh out.png t1 t2 ... (最多 10 个时间点，渲静帧并拼成 5 列联系表)
out=$1; shift; ins=(); i=0; f=""; lay=""
for t in "$@"; do
  python3 tools/render.py index.html qa/s_$t.png --still $t --size 1080x1920 >/dev/null 2>&1 || echo "fail $t"
  ins+=(-i qa/s_$t.png); f+="[$i]scale=360:640[v$i];"; lay+="[v$i]"; i=$((i+1))
done
pos=""; for j in $(seq 0 $((i-1))); do pos+="$(( (j%5)*360 ))_$(( (j/5)*640 ))|"; done
ffmpeg -v error -y "${ins[@]}" -filter_complex "${f}${lay}xstack=inputs=$i:layout=${pos%|}" "$out"

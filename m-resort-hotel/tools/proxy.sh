f=$1; o=$2/$(basename $f .mp4).mp4
[ -s $o ] && exit 0
ffmpeg -v error -y -i $f -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,fps=30" -c:v libx264 -preset veryfast -crf 19 -pix_fmt yuv420p -c:a aac -b:a 160k -ar 48000 $o.tmp.mp4 && mv $o.tmp.mp4 $o

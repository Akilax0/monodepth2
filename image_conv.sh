while getopts f: flag
do
	case "${flag}" in
		f) file=${OPTARG};;
	esac
done
echo "file : ${file}";
mod=${file%.*}".jpg";
echo "jpg : ${mod}";

convert -quality 92 -sampling-factor 2x2,1x1,1x1 ${file} ${mod} && rm ${file}

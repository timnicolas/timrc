dj_initProjDir () {
	create=(
		"templates"
		"static"
		"static/css"
		"static/js"
		"static/img"
	)
	for i in "${create[@]}"; do
		echo "$i"
		mkdir ${i}
		touch ${i}/.empty
	done
}


dj_initAppDir () {
	create=(
		"templates"
		"templates/$1"
		"static"
		"static/$1"
		"static/$1/css"
		"static/$1/js"
		"static/$1/img"
	)
	for i in "${create[@]}"; do
		echo "$i"
		mkdir ${i}
		touch ${i}/.empty
	done
	echo "urls.py"
	touch urls.py
}

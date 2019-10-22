dj_initProjDir () {
	create=(
		"templates"
		"static"
		"static/css"
		"static/js"
		"static/img"
		"media"
	)
	for i in "${create[@]}"; do
		echo "$i"
		mkdir ${i}
		touch ${i}/.empty
	done
}


dj_initAppDir () {
	createDir=(
		"templates"
		"templates/$1"
		"static"
		"static/$1"
		"static/$1/css"
		"static/$1/js"
		"static/$1/img"
	)
	createFiles=(
		"urls.py"
		"forms.py"
	)
	for i in "${createDir[@]}"; do
		echo "$i"
		mkdir ${i}
		touch ${i}/.empty
	done
	for i in "${createFiles[@]}"; do
		echo "$i"
		touch ${i}
	done
}

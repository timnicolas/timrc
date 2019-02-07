"""""""""""""""""""""""""""""""""""""ctrlD""""""""""""""""""""""""""""""""""""""
function! TimReplace2words(word, replace1, replace2)
	if a:word == a:replace1
		:normal diw
		exe ':normal i' . a:replace2
	elseif a:word == a:replace2
		:normal diw
		exe ':normal i' . a:replace1
	endif
endfunction
function! TimAddBefore(replace_word)
	:normal l
	:normal b
	:normal b
	let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
	if char_act =~# '\w'
		let word = expand("<cword>")
	else
		return
	endif
	if word == a:replace_word
		:normal diwx
	else
		:normal w
		exe ':normal i' . a:replace_word . ' '
		:normal l
	endif
endfunction

"invert sign (+ -, * /, ...) <C-d>
imap <C-d> <C-o>:call SergeInvertSign()<CR>
nmap <C-d> :call SergeInvertSign()<CR>
function! SergeInvertSign()
	let line = getline('.')
	let col = col('.')
	"	exe ':normal 6|'
	let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
	if char_act == '+'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '='
			:normal h
			:normal r-
		elseif char_act == '+'
			:normal r-
			:normal h
			:normal r-
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '+'
				:normal r-
				:normal l
				:normal r-
			else
				:normal l
				:normal r-
			endif
		endif
	elseif char_act == '-'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act =~# '\d'
			:normal h
			:normal x
		elseif char_act == '='
			:normal h
			:normal r+
		elseif char_act == '>'
			:normal h
			:normal xx
			:normal i.
		elseif char_act == '-'
			:normal r+
			:normal h
			:normal r+
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '-'
				:normal r+
				:normal l
				:normal r+
			else
				:normal l
				:normal r+
			endif
		endif
	elseif char_act =~# '\d'
		let i = 0
		while char_act =~# '\d' || char_act == '.'
			let i += 1
			:silent normal h
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if col('.') == 1
				break
			endif
		endwhile
		if char_act == '-'
			:normal x
			:normal h
			if col('.') == 1
				let i -= 1
			endif
		elseif col('.') == 1
			":normal h
			:normal i-
			:normal l
		elseif char_act =~# '\w'
			:normal hl
		else
			:normal l
			:normal i-
		endif
		while i > 0
			let i -= 1
			:normal l
		endwhile
	elseif char_act == '|'
		:normal r&
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '|'
			:normal r&
			:normal h
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '|'
				:normal r&
				:normal l
			else
				:normal l
			endif
		endif
	elseif char_act == '&'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act =~# '\w'
			:normal h
			:normal r*
		else
			:normal h
			:normal r|
			:silent normal l
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '&'
				:normal r|
				:normal h
			else
				:silent normal hh
				let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
				if char_act == '&'
					:normal r|
					:normal l
				else
					:normal l
					:normal r^
				endif
			endif
		endif
	elseif char_act == '^'
		:normal r|
	elseif char_act == '*'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act =~# '\w'
			:normal h
			:normal r&
		elseif char_act == '*'
			:normal x
			:normal h
		elseif char_act == ')'
			:normal h
		elseif char_act == '='
			:normal h
			:normal r/
		else
			:normal h
			:normal r/
		endif
	elseif char_act == '/'
		:normal r%
	elseif char_act == '%'
		:normal r*
	elseif char_act == '<'
		:normal r>
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '<'
			:normal r>
			:normal h
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '<'
				:normal r>
				:normal l
			else
				:normal l
			endif
		endif
	elseif char_act == '>'
		:normal r<
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '>'
			:normal r<
			:normal h
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '>'
				:normal r<
				:normal l
			elseif char_act == '-'
				:normal xx
				:normal i.
			else
				:normal l
			endif
		endif
	elseif char_act == '.'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act =~# '[a-zA-Z_]'
			:normal h
			:normal x
			:normal i->
			:normal h
		elseif char_act =~# '\d'
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act =~# '\d'
				call SergeInvertSign()
				:normal l
			else
				:normal l
				:normal x
				:normal i->
				:normal h
			endif
		else
			:normal h
		endif
	elseif char_act == '='
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '='
			:normal h
			:normal r!
		else
			:silent normal hh
			let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
			if char_act == '='
				:normal r!
				:normal l
			elseif char_act == '!'
				:normal r=
				:normal l
			elseif char_act == '+'
				:normal r-
				:normal l
			elseif char_act == '-'
				:normal r+
				:normal l
			elseif char_act == '*'
				:normal r/
				:normal l
			elseif char_act == '/'
				:normal r*
				:normal l
			elseif char_act == '>'
				:normal r<
				:normal l
			elseif char_act == '<'
				:normal r>
				:normal l
			else
				:normal l
			endif
		endif
	elseif char_act == '!'
		:silent normal l
		let char_act = matchstr(getline('.'), '\%' . col('.') . 'c.')
		if char_act == '='
			:normal h
			:normal r=
		else
			:normal h
		endif
	elseif char_act == "'"
		:normal r"
	elseif char_act == '"'
		:normal r'
	elseif char_act =~# '\w'
		let word = expand("<cword>")
		call TimReplace2words(word, 'SUCCESS', 'ERROR')
		call TimReplace2words(word, 'Success', 'Error')
		call TimReplace2words(word, 'success', 'error')
		call TimReplace2words(word, 'TRUE', 'FALSE')
		call TimReplace2words(word, 'True', 'False')
		call TimReplace2words(word, 'true', 'false')
		if word == 'unsigned'
			:normal diwx
		elseif word == 'int' || word == 'char' || word == 'short' ||
					\word == 'long'
			call TimAddBefore('unsigned')
		elseif word == 'else'
			:normal diwx
		elseif word == 'if'
			call TimAddBefore('else')
		endif
	endif
endfunction
"""""""""""""""""""""""""""""""""""""ctrlD""""""""""""""""""""""""""""""""""""""

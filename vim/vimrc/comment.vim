"""""""""""""""""""""""""""""""""""""comment""""""""""""""""""""""""""""""""""""
"<leader>/			comment region
vmap <leader>/ :call SergeCommentRegion()<CR>
nmap <leader>/ :call SergeCommentRegion()<CR>
function! SergeCommentRegion() range
	let comment = '#'
	if expand('%:e') == 'c' || expand('%:e') == 'h' || expand('%:e') == 'cpp' || expand('%:e') == 'js'
		let comment = '\/\/'
	elseif expand('%:e') == 'vim' || expand('%:t') == '.vimrc'
		let comment = '"'
	elseif expand('%:t') == '.emacs' || expand('%:e') == 'lisp'
		let comment = ';'
	endif
	exe ':silent!' . a:firstline . ',' . a:lastline . 's/^\(\s*' .
				\l:comment . '\)\@!/' . l:comment . '/g'
	:silent!/dsfahfdkljhfklahsflahsf
endfunction

"<leader>\			uncomment region
vmap <leader>\ :call SergeDecommentRegion()<CR>
nmap <leader>\ :call SergeDecommentRegion()<CR>
function! SergeDecommentRegion() range
	let comment = '#'
	if expand('%:e') == 'c' || expand('%:e') == 'h' || expand('%:e') == 'cpp' || expand('%:e') == 'js'
		let comment = '\/\/'
	elseif expand('%:e') == 'vim' || expand('%:t') == '.vimrc'
		let comment = '"'
	elseif expand('%:t') == '.emacs' || expand('%:e') == 'lisp'
		let comment = ';'
	endif
	exe ':silent!' . a:firstline . ',' . a:lastline . 's/^' . l:comment . '//g'
	exe ':silent!' . a:firstline . ',' . a:lastline . 's/^\s\+\zs' . l:comment .
				\'\ze//g'
	:silent!/dsfahfdkljhfklahsflahsf
endfunction
"""""""""""""""""""""""""""""""""""""comment""""""""""""""""""""""""""""""""""""

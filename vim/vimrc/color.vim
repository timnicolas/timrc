"""""""""""""""""""""""""""""""""""""info"""""""""""""""""""""""""""""""""""""""
"0       0       Black
"1       4       DarkBlue
"2       2       DarkGreen
"3       6       DarkCyan
"4       1       DarkRed
"5       5       DarkMagenta
"6       3       Brown, DarkYellow
"7       7       LightGray, LightGrey, Gray, Grey
"8       0*      DarkGray, DarkGrey
"9       4*      Blue, LightBlue
"10      2*      Green, LightGreen
"11      6*      Cyan, LightCyan
"12      1*      Red, LightRed
"13      5*      Magenta, LightMagenta
"14      3*      Yellow, LightYellow
"15      7*      White

"for 256 colors https://jonasjacek.github.io/colors/

"https://alvinalexander.com/linux/vi-vim-editor-color-scheme-syntax

"to know inforation about the color under cursor:
" :echo "hi<" . synIDattr(synID(line("."),col("."),1),"name") . '> trans<' . synIDattr(synID(line("."),col("."),0),"name") . "> lo<" . synIDattr(synIDtrans(synID(line("."),col("."),1)),"name") . ">"
"""""""""""""""""""""""""""""""""""""info"""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""
if g:_enable_color_all == 0
	finish
endif

syntax enable
hi CursorLine ctermbg=237 cterm=none
hi PreProc ctermfg=red

"color function
augroup Syntax
	autocmd!
"""""""""""""""""""""""""""""""""""""language all"""""""""""""""""""""""""""""""
"""""""""""""""""""""""""""""""""""""language all"""""""""""""""""""""""""""""""
	" extra whitespaces in red
	autocmd BufEnter * 	hi ExtraWhitespace ctermbg=red guibg=red
	autocmd BufEnter *	match ExtraWhitespace /\s\+$/

	" number and float color
	autocmd BufEnter * 	hi Number ctermfg=DarkGreen
	autocmd BufEnter * 	hi Float ctermfg=DarkGreen
"""""""""""""""""""""""""""""""""""""language C/cpp"""""""""""""""""""""""""""""
	autocmd BufEnter * if (expand('%:e') == 'h' || expand('%:e') == 'c' ||
				\expand('%:e') == 'cpp')

	" function call colored
	autocmd BufEnter * 	syn match Color_function /\zs\w\+\ze(/
	autocmd BufEnter * 	hi Color_function ctermfg=Blue

	" CONST coloration
	autocmd BufEnter * 	syn match Color_define_name /\<[A-Z_][A-Z_0-9]*\>/
	autocmd BufEnter * 	hi Color_define_name ctermfg=LightBlue

	" color word end with _t (type_t)
	autocmd BufEnter * 	syn match Color_typedef /\(\w\)\@<!\zs[tseu]_\w\+\ze\|\zs\w\+_t\ze\(\w\)\@!/
	autocmd BufEnter * 	hi Color_typedef ctermfg=LightGreen

	" color operator (&&, ||, pointer, ...)
	autocmd BufEnter * 	syn match Color_operator /&\||\|\w\zs\*\+\ze\|\zs\*\+
				\\ze\w\|\zs\*\+\ze)\|(\zs\*\+\ze\|\zs\*\+\ze(/
	" ) )
	autocmd BufEnter * 	hi Color_operator ctermfg=Red

	autocmd BufEnter * endif
"""""""""""""""""""""""""""""""""""""language C/cpp"""""""""""""""""""""""""""""


"""""""""""""""""""""""""""""""""""""language python""""""""""""""""""""""""""""
	autocmd BufEnter * if (expand('%:e') == 'py')

	" function call colored
	autocmd BufEnter * 	syn match Color_function /\zs\w\+\ze(/
	autocmd BufEnter * 	hi Color_function ctermfg=Blue

	" CONST coloration
	autocmd BufEnter * 	syn match Color_define_name /\<[A-Z_][A-Z_0-9]*\>/
	autocmd BufEnter * 	hi Color_define_name ctermfg=LightBlue

	" color python operator
	autocmd BufEnter * 	hi pythonOperator ctermfg=Yellow

	autocmd BufEnter * endif
"""""""""""""""""""""""""""""""""""""language python""""""""""""""""""""""""""""
augroup END
"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""

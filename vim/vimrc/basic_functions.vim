"""""""""""""""""""""""""""""""""""""basic commands"""""""""""""""""""""""""""""
"help <leader>h :SergeHelp
nmap <leader>h :exe "tabnew " . g:help_vim_file<CR>
command! TimHelp exe "tabnew " . g:help_vim_file

"setting <leader>s :SergeSetting
nmap <leader>s :exe "tabnew " . g:setting_vim_file<CR>
command! TimSetting exe "tabnew " . g:setting_vim_file

"binary mode
nmap <leader>b :%!xxd<CR>

"vim '+Line' to open vim with highlight line
command! Line set invcursorline
"cursor line <F4>
nmap <F4> :set invcursorline<CR>
imap <F4> <esc>:set invcursorline<CR>

"relative number : <F3>
nmap <F3> :set invrelativenumber<CR>
imap <F3> <esc>:set invrelativenumber<CR>i
"""""""""""""""""""""""""""""""""""""basic commands"""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""save/quit""""""""""""""""""""""""""""""""""
"easy save
command! W w
command! Q q
command! WQ wq
command! Wq wq
command! WA wa
command! Wa wa
command! WQA wqa
command! WQa wqa
command! Wqa wqa
command! WqA wqa
command! XA xa
command! Xa xa
"""""""""""""""""""""""""""""""""""""save/quit""""""""""""""""""""""""""""""""""
"
"""""""""""""""""""""""""""""""""""""tab buffer"""""""""""""""""""""""""""""""""
"change buffer (<C-w> + up/down/right/left || hjkl)
"	right <C-w> l
nmap <C-w><right> <C-w>l
nmap <C-w><C-l> <C-w>l
map <C-l> <C-w>l
"	left <C-w> h
nmap <C-w><left> <C-w>h
nmap <C-w><C-h> <C-w>h
map <C-h> <C-w>h
"	up <C-w> k
nmap <C-w><up> <C-w>k
nmap <C-w><C-k> <C-w>k
map <C-k> <C-w>k
"	down <C-w> j
nmap <C-w><down> <C-w>j
nmap <C-w><C-j> <C-w>j
map <C-j> <C-w>j
"""""""""""""""""""""""""""""""""""""tab buffer"""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""fullscreen"""""""""""""""""""""""""""""""""
let g:is_fullscreen=0
function! TimFullScreen()
	if g:is_fullscreen == 0
		wincmd |
		wincmd _
		let g:is_fullscreen=1
	else
		wincmd =
		let g:is_fullscreen=0
	endif
endfunction
nmap <C-w>z :call TimFullScreen()<CR>
imap <C-w>z <C-o>:call TimFullScreen()<CR>
vmap <C-w>z <C-o>:call TimFullScreen()<CR>
"""""""""""""""""""""""""""""""""""""fullscreen"""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""fast move""""""""""""""""""""""""""""""""""
"go to the end of line <S-right>
nmap <S-right> $
imap <S-right> <esc>A
vmap <S-right> $
"go to the begining of line <S-right>
nmap <S-left> ^
imap <S-left> <esc>I
vmap <S-left> ^
"fast move of 5 char up <S-up>
nmap <S-up> :-5<CR>
imap <S-up> <C-o>:-5<CR>
vmap <S-up> <up><up><up><up><up>
"fast move of 5 char down <S-down>
nmap <S-down> :+5<CR>
imap <S-down> <C-o>:+5<CR>
vmap <S-down> <down><down><down><down><down>
"""""""""""""""""""""""""""""""""""""fast move""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""tools for vimscript""""""""""""""""""""""""
"keep cursor place
let g:last_filename = expand('%')
let g:first_line_visible = line('w0') + g:min_number_line_ar_cur
let g:save_pos = getpos('.')
function! SetCursorPlaceSave()
	let g:last_filename = expand('%')
	let g:first_line_visible = line('w0') + g:min_number_line_ar_cur
	let g:save_pos = getpos('.')
endfunction
function! SetCursorPlaceGo()
	exe ':b ' . g:last_filename
	exe ':' . g:first_line_visible
	:normal zt
	call setpos('.', g:save_pos)
endfunction
"""""""""""""""""""""""""""""""""""""tools for vimscript""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""completion"""""""""""""""""""""""""""""""""
"';' at the end of line width <leader>;
nmap <leader>; :call PointVirgule()<CR>
function! PointVirgule()
	call SetCursorPlaceSave()
	let line_before = line('.')
	if search(';\s*\n', 'n', line('.')) == line_before
		exe ':' . line_before . 's/;\s*\n/\r'
	else
		exe ':' . line_before . 's/\s*\n/;\r'
	endif
	:silent! /cgvhadgfhadgfjksahfjkdhfjkdshfHL
	call SetCursorPlaceGo()
endfunction

" if {<CR> putt corect {...}
imap {<CR>  {<CR>}<Esc>O
"create block <leader>[([{'"]
vmap <leader>( <Esc>`<i(<Esc>`>a<right>)<Esc>
vmap <leader>[ <Esc>`<i[<Esc>`>a<right>]<Esc>
vmap <leader>' <Esc>`<i'<Esc>`>a<right>'<Esc>
vmap <leader>" <Esc>`<i"<Esc>`>a<right>"<Esc>
nmap <leader>{ o}<Esc><up>O{<Esc>=2<down><down>
vmap <leader>{ :call PutAcolade()<CR>
function! PutAcolade() range
	exe ':' . a:firstline
	:normal O
	exe ':' . line('.') . 's/^\s*/{'
	let line_plus1 = a:lastline + 1
	exe ':' . l:line_plus1
	:normal o
	let line_plus1 = line('.') + 1
	exe ':' . line('.') . 's/^\s*/}'
	let rangeIndent = a:lastline - a:firstline + 2
	exe ':normal =' . l:rangeIndent . 'k'
endfunction
"""""""""""""""""""""""""""""""""""""completion"""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""abreviate""""""""""""""""""""""""""""""""""
"main auto with mainn
ab mainn int<tab><tab><tab>main(int ac, char **av)<CR>
			\{<CR>
			\<CR>
			\return (0);<CR>
			\}<esc>4=<up>2<down>i

"test file with testt
ab testt #include <stdio.h><CR>
			\#include <stdlib.h><CR>
			\#include <unistd.h><CR>
			\#include <limits.h><CR>
			\#include <string.h><CR>
			\#include <ctype.h><CR>
			\<CR>
			\int<tab><tab><tab>main(int ac, char **av)<CR>
			\{<CR>
			\int<tab><tab>i;<CR>
			\<CR>
			\(void)ac;<CR>
			\(void)av;<CR>
			\(void)i;<CR>
			\<CR>
			\<tab>return (0);<CR>
			\}<esc>16=<up>14<down>i
"""""""""""""""""""""""""""""""""""""abreviate""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""
let g:numcolor=0
function! TimColor(...)
	let l:word = get(a:, 1, '0')
	if l:word == '0'
		echo 'TimColor(word, fg, bg)'
		return
	endif
	let l:fg = get(a:, 2, 'none')
	if l:fg != ''
		let l:fg = ' ctermfg=' . l:fg
	endif
	let l:bg = get(a:, 3, 'none')
	if l:bg != ''
		let l:bg = ' ctermbg=' . l:bg
	endif
	exe 'hi Color' . g:numcolor . l:fg . l:bg
	exe 'match Color' . g:numcolor . ' /' . l:word . '/'
	let g:numcolor = g:numcolor + 1
endfunction
"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""

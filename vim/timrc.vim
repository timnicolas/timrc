"""""""""""""""""""""""""""""""""""""mapleader""""""""""""""""""""""""""""""""""
" set mapleader
let mapleader = ","
if has('terminal') && has('macunix')
	set termwinkey=<C-L>
endif
"""""""""""""""""""""""""""""""""""""mapleader""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""files""""""""""""""""""""""""""""""""""""""
" path to timrc-vim
let s:path = expand('<sfile>:p:h')

let g:help_vim_file="" . s:path . '/timrc_help.vim'
let g:setting_vim_file="" . s:path . '/vimrc/setting.vim'
"""""""""""""""""""""""""""""""""""""files""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""source"""""""""""""""""""""""""""""""""""""
exec "source " . s:path . '/vimrc/setting.vim'
exec "source " . s:path . '/vimrc/basic_settings.vim'
exec "source " . s:path . '/vimrc/basic_functions.vim'
exec "source " . s:path . '/vimrc/plugin.vim'
exec "source " . s:path . '/vimrc/ctrlD.vim'
exec "source " . s:path . '/vimrc/comment.vim'
exec "source " . s:path . '/vimrc/color.vim'
"""""""""""""""""""""""""""""""""""""source"""""""""""""""""""""""""""""""""""""

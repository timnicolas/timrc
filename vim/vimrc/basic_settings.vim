"""""""""""""""""""""""""""""""""""""basic settings"""""""""""""""""""""""""""""
colorscheme ron
set nocompatible "more vim function
filetype off
set noautoindent "indent gestion with plugin
filetype indent plugin on
set cindent "indent for c files
set smartindent "autoindent
syn on "coloration syntax
set number "number of line
"min line visible around cursor
exe 'set so=' . g:min_number_line_ar_cur
if g:enable_mouse == 1
	set mouse=a "mouse on

else
	set mouse=
endif
if g:setHighlightLine == 1
	set cursorline "highlight  line

else
	set nocursorline
endif
set tabstop=4 "tab size
set shiftwidth=4 "tab size
set noexpandtab "no replace tab to space
set omnifunc=syntaxcomplete#Complete "autocompletion (<C-n>)
set showcmd "see command
"set rulerformat=%27(%{strftime('%a\ %e\ %b\ %I:%M\ %p')}\ %2l,%-2(%c%V%)\ %P%)
set showmode "mode in status bar
set shm=a "intelligent print of avertissement
set laststatus=2 "show always status bar (not only on split mode
set cmdheight=1 "size of command bar
if g:max_size_line > 0 "column 81 in red
	exe 'set colorcolumn=' . g:max_size_line
endif
set autowrite "auto save when change buffer
set clipboard=unnamed "to copy and paste
if g:highlight_search == 1
	set hlsearch "highlight search
else
	set nohlsearch
endif
set incsearch "highlight when typing command (not only after)
set backspace=2 "backspace
set noswapfile "no swap file
set noignorecase "no ignore case
au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") |
			\exe "normal! g`\"" | endif "remember position in file
"""""""""""""""""""""""""""""""""""""basic settings"""""""""""""""""""""""""""""

"plugin
"Vundle
"	:source ~/.vimrc
"	:PluginInstall
":plugin to install plugin
command! Plugin call Plugin_install_()
function! PLugin_install_()
	:source ~/.vimrc
	:PluginInstall
endfunction
set rtp+=~/.vim/bundle/Vundle.vim

"""""""""""""""""""""""""""""""""""""plugin list""""""""""""""""""""""""""""""""
call vundle#begin()
Plugin 'gmarik/Vundle.vim'


"pour la barre en bas de couleur
if g:_enablelightline == 1
	Plugin 'itchyny/lightline.vim'
endif

"gestionaire de fichier
if g:_enableNERDTree == 1
	Plugin 'scrooloose/nerdtree'
endif

"pour colorer les nom de couleur ex #FFFFFF #00FF00
if g:_enablecolorizer == 1
	Plugin 'vim-scripts/colorizer'
endif

"correction des erreurs de code
if g:_enablesyntastic == 1
	Plugin 'vim-syntastic/syntastic'
	Plugin 'myint/syntastic-extras'
endif

"git diff
if g:_enablegitgutter == 1 
	Plugin 'airblade/vim-gitgutter'
endif

"indentation python
if g:_enablePythonIndent == 1
	Plugin 'indentpython.vim'
"	Plugin 'Vimjas/vim-python-pep8-indent'
endif

call vundle#end()
"""""""""""""""""""""""""""""""""""""plugin list""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""plugin commands""""""""""""""""""""""""""""
"	nerdtree
"		open/close nerdtree <leader>g
if g:_enableNERDTree == 1
	let g:state_NerdTree = 0
	nmap <leader>g :call NavFichier()<CR><C-w>=
	function! NavFichier()
		if (g:state_NerdTree == 0)
			:NERDTree
			let g:state_NerdTree = 1
		else
			:NERDTreeClose
			let g:state_NerdTree = 0
		endif
	endfunction
endif

"	GitGutter
nmap <F5> :GitGutterToggle<CR>
command! Diff :GitGutterEnable

if g:_enablesyntastic == 1
	set statusline+=%#warningmsg#
	set statusline+=%{SyntasticStatuslineFlag()}
	set statusline+=%*

	let g:syntastic_always_populate_loc_list = 1
	let g:syntastic_check_on_open = 1
	let g:syntastic_check_on_wq = 0

	"height of error windows
	let g:syntastic_loc_list_height = 5
	"no highlight text
	let g:syntastic_enable_highlighting = 0

	function! ToggleErrors()
	    if empty(filter(tabpagebuflist(), 'getbufvar(v:val, "&buftype") is# "quickfix"'))
			" No location/quickfix list shown, open syntastic error location panel
			Errors
	    else
			lclose
	    endif
	endfunction
	nmap <silent> <F2> :call ToggleErrors()<CR>
	imap <silent> <F2> <C-o>:call ToggleErrors()<CR>
	vmap <silent> <F2> :call ToggleErrors()<CR>
endif
"""""""""""""""""""""""""""""""""""""plugin commands""""""""""""""""""""""""""""

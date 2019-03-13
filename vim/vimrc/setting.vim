"""""""""""""""""""""""""""""""""""""general""""""""""""""""""""""""""""""""""""
"min number of line around cursor
let g:min_number_line_ar_cur = 4
"color column (for max size line) 0 to off (example: 81 or 121)
if (expand('%:e') == 'h' || expand('%:e') == 'c' || expand('%:e') == 'cpp')
	let g:max_size_line=81
else
	let g:max_size_line=121
endif
"enable or diable mouse
let g:enable_mouse=1
"highlight search
let g:highlight_search=1
"highlight line
let g:setHighlightLine=0
"""""""""""""""""""""""""""""""""""""general""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""
"enable more color
let g:_enable_color_all=1
"""""""""""""""""""""""""""""""""""""color""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""plugin"""""""""""""""""""""""""""""""""""""
"activer ou desactiver un plugin
"   NERDTree (navigateur de fichier)
let g:_enableNERDTree=1
"   lightline (barre colore en bas de l'ecran)
let g:_enablelightline=1
"   colorizer (les couleurs se colorent #FF00FF #120499)
let g:_enablecolorizer=1
"   syntastic (correction code)
let g:_enablesyntastic=1 " ENABLE/DISABLE SYNTAX CHECKER
"   git-gutter view added and deleted lines in git
let g:_enablegitgutter=1
"   auto indent for python
let g:_enablePythonIndent=1

"taille de la fenetre nerdtree
let g:NERDTreeWinSize=27

"syntastic error windows (0 off, 1 open/close auto, 2 close auto)
let g:syntastic_auto_loc_list = 1
"pour supprimer les erreurs syntastic preciser tout les dossiers a header
let g:syntastic_c_include_dirs = [
            \'../includes',
            \'includes',
            \'commun/includes',
            \'../commun/includes',
            \'../../commun/includes',
            \'../../../commun/includes',
            \'commun',
            \'../commun',
            \'../../commun',
            \'../../../commun',
            \'*/includes',
            \'*/*includes',
            \'../lib/includes',
            \'lib/includes',
            \'includes',
            \'libft/includes/',
            \'../libft/includes/',
            \'../../includes',
            \'../../libft/includes',
            \'../../libft',
            \'../../../includes',
            \'../../../libft/includes',
            \'../../../libft',
            \'libft/lib/includes/',
            \'../libft/lib/includes/',
            \'../../includes',
            \'../../libft/lib/includes',
            \'../../libft',
            \'../../../includes',
            \'../../../libft/lib/includes',
            \'../../../libft',
            \'minilibx',
            \'../minilibx',
            \'../../minilibx',
            \'../../../minilibx',
            \'minilibx_macos',
            \'../minilibx_macos',
            \'../../minilibx_macos',
            \'../../../minilibx_macos',
            \]
let g:syntastic_cpp_include_dirs = g:syntastic_c_include_dirs
"""""""""""""""""""""""""""""""""""""plugin"""""""""""""""""""""""""""""""""""""

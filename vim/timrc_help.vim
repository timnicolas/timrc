"""""""""""""""""""""""""""""""""""""general""""""""""""""""""""""""""""""""""""
" , -> <leader>

" :TimHelp
" <leader>h   open help

" :TimSetting
" <leader>s   open settings

" :call Timcolor(word, fg=none, bg=none)  color all 'word' with fg and bg

" <leader>b   convert binary to readable file (:%!xxd)

" :Line
" <F4>        show line

" <F3>        relative number

" <C-d>       invert sign (+ -, true false, >= <=, ...)

" <leader>/   comment region
" <leader>\   uncomment region
" <leader>;   put or remove ; at the end of line
" <leader>[(['"]  (visual mode) put text in (), '', ...
" <leader>{   put text in {\n...\n} (correct indentation)
" {<CR>       (insert mode) put {...} correctly

" mainn<tab>  (insert mode) write a main function (C language)
" testt<tab>  (insert mode) write a main function with usefull include (C language)
"""""""""""""""""""""""""""""""""""""general""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""movement"""""""""""""""""""""""""""""""""""
""""" buffer
" <C-w><right>
" <C-w>l      go to buffer right
" same for up/down/left
" <C-w>z	  toogle fullscreen

""""" other
" <S-up>      go tu 5 line up
" <S-down>    go to 5 line down
" <S-right>   go to the end of line
" <S-left>    go to the begining of line
"""""""""""""""""""""""""""""""""""""movement"""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""plugin"""""""""""""""""""""""""""""""""""""
" :Plugin     install/update plugins

" NerdTree (file navigator)
" <leader>g  enable/disable NerdTree

" GitGutter (git diff)
" <F5>       enable/disable GitGutter

" Syntastic (syntax checker)
" <F2>      enable/disable Syntastic
" :let syntastic_auto_loc_list=0  disable syntastic win
" :let syntastic_auto_loc_list=1  enable syntastic win
"""""""""""""""""""""""""""""""""""""plugin"""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""mapped key"""""""""""""""""""""""""""""""""
" list of all mapped key with timrc-vim
" :call TimColor
" :TimHelp
" :TimSetting
" :Plugin
" :Line
" ,
" ,b
" ,g
" ,h
" ,s
" ,/
" ,\
" ,;
" ,(
" ,[
" ,{
" ,'
" ,"
" <F2>
" <F3>
" <F4>
" <F5>
" <C-d>
" {<CR>
" mainn<tab>
" testt<tab>
" <C-w>h
" <C-w>j
" <C-w>k
" <C-w>l
" <C-w><left>
" <C-w><down>
" <C-w><up>
" <C-w><right>
" <C-w>z
" <S-left>
" <S-down>
" <S-up>
" <S-right>
"""""""""""""""""""""""""""""""""""""mapped key"""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""vim""""""""""""""""""""""""""""""""""""""""
""""" mode
" i            insert mode
" I            insert mode (begining of line)
" a            insert mode (next charactere)
" A            insert mode(end of line)
" c            like d then insert mode
" s            del char and insert mode
" S            del line and insert mode
" <C-o>        in insert mode go to normal mode for one command
" <esc>        normal mode
" v            visual mode
" V            visual mode (line mode)
" <C-v>        visual mode (square mode)

""""" tab
" :tabnew      new tab
" :tabclose    close tab
" :tabmove +#  move tab to right (# time)
" :tabmove -#  move tab to left (# time)
" :tabm        move tab to last position
" :tabm #      move tab to the #th position
" :tabr        go to first tab
" :tabl        go to last tab
" gt           next tab
" gT           prev tab

""""" term
" :term          open terminal (horizontal split)
" :term ++curwin open terminal in current window

""""" cscope (language C database)

""""" folding commands
" zf#j   creates a fold from the cursor down # lines.
" zf/    string creates a fold from the cursor to string .
" zj     moves the cursor to the next fold.
" zk     moves the cursor to the previous fold.
" za     toggle a fold at the cursor.
" zo     opens a fold at the cursor.
" zO     opens all folds at the cursor.
" zc     closes a fold under cursor.
" zm     increases the foldlevel by one.
" zM     closes all open folds.
" zr     decreases the foldlevel by one.
" zR     decreases the foldlevel to zero -- all folds will be open.
" zd     deletes the fold at the cursor.
" zE     deletes all folds.
" [z     move to start of open fold.
" ]z     move to end of open fold.
"""""""""""""""""""""""""""""""""""""vim""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""key""""""""""""""""""""""""""""""""""""""""
" notation in vimrc
" C					Control : <C-w>
" S					Shift : <S-k>
" A / M				Alt : <A-tab>
" <BS>				Backspace
" <Tab>				Tab
" <CR>				Enter
" <Enter>			Enter
" <Return>			Enter
" <Esc>				Escape
" <Space>			Space
" <Up>				Up arrow
" <Down>			Down arrow
" <Left>			Left arrow
" <Right>			Right arrow
" <F1> - <F12>		Function keys 1 to 12
" #1, #2..#9,#0		Function keys F1 to F9, F10
" <Insert>			Insert
" <Del>				Delete
" <Home>			Home
" <End>				End
" <PageUp>			Page-Up
" <PageDown>		Page-Down
" <bar>				the '|' character, which otherwise needs to be escaped '\|'
"""""""""""""""""""""""""""""""""""""key""""""""""""""""""""""""""""""""""""""""

"""""""""""""""""""""""""""""""""""""variable"""""""""""""""""""""""""""""""""""
" g:varname			The variable is global
" s:varname			The variable is local to the current script file
" w:varname			The variable is local to the current editor window
" t:varname			The variable is local to the current editor tab
" b:varname			The variable is local to the current editor buffer
" l:varname			The variable is local to the current function
" a:varname			The variable is a parameter of the current function
" v:varname			The variable is one that Vim predefines
"""""""""""""""""""""""""""""""""""""variable"""""""""""""""""""""""""""""""""""

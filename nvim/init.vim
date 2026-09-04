" config nvim independante de vim/timrc.vim (nvim a deja beaucoup de defauts modernes en plus ;
" cf lua/config/options.vim pour ce qui est repris volontairement de timrc.vim)
" (rtp += ce repo pour que require() trouve $TIMRC_NVIM/lua/*)
if !empty($TIMRC_NVIM)
	let &runtimepath = $TIMRC_NVIM . ',' . &runtimepath
	let mapleader = ","
	lua require('config.lazy')
endif

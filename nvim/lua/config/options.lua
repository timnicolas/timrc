-- config nvim native, independante de vim/timrc.vim (voir le message de commit / la conv pour le pourquoi)
local opt = vim.opt

-- affichage
opt.number = true
opt.termguicolors = true -- vraies couleurs (tmux passe RGB, cf ~/.tim/tmux/tmux.conf)
opt.signcolumn = "yes" -- colonne fixe pour les signes git/LSP (evite le texte qui saute)
opt.scrolloff = 8
opt.cursorline = true

-- indentation (tabs, comme sur l'ancienne config vim)
opt.tabstop = 4
opt.shiftwidth = 4
opt.expandtab = false
opt.smartindent = true

-- edition
opt.mouse = "a"
opt.clipboard = "unnamedplus" -- copier/coller avec le presse-papier systeme
opt.ignorecase = false
opt.incsearch = true
opt.updatetime = 250 -- diagnostics LSP plus reactifs
opt.splitright = true
opt.splitbelow = true
opt.undofile = true -- historique d'annulation persistant entre sessions (pas dans l'ancienne config vim)

-- garde la position du curseur en reouvrant un fichier (equivalent de l'autocmd vim)
vim.api.nvim_create_autocmd("BufReadPost", {
	callback = function()
		local mark = vim.api.nvim_buf_get_mark(0, '"')
		local lcount = vim.api.nvim_buf_line_count(0)
		if mark[1] > 0 and mark[1] <= lcount then
			vim.api.nvim_win_set_cursor(0, mark)
		end
	end,
})

-- commandes "easy save" (repris de timrc.vim, aucun cout/conflit)
for _, cmd in ipairs({ "W", "Q", "WQ", "Wq", "WA", "Wa", "WQA", "WQa", "Wqa", "WqA", "XA", "Xa" }) do
	vim.api.nvim_create_user_command(cmd, cmd:lower(), {})
end

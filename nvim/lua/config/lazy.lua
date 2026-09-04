-- bootstrap lazy.nvim (plugin manager), cf https://lazy.folke.io
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
	vim.fn.system({
		"git", "clone", "--filter=blob:none",
		"https://github.com/folke/lazy.nvim.git",
		"--branch=stable",
		lazypath,
	})
end
vim.opt.rtp:prepend(lazypath)

require("config.options")

require("lazy").setup({
	spec = { { import = "plugins" } },
	-- lazy par defaut (evenement VeryLazy, quasi instantane) : evite qu'un plugin non encore
	-- installe soit charge en plein milieu de lazy.setup() au tout premier lancement
	defaults = { lazy = true },
	install = { colorscheme = { "catppuccin" } },
	checker = { enabled = false },
})

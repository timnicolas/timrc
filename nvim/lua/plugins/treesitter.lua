return {
	"nvim-treesitter/nvim-treesitter",
	-- branche "main" = reecriture recente qui a retire l'API nvim-treesitter.configs utilisee ici
	branch = "master",
	-- pas de build = ":TSUpdate" : perturbe le sync headless (cf install_nvim.sh), et
	-- ensure_installed ci-dessous installe deja les parsers tout seul au premier chargement
	event = "VeryLazy",
	config = function()
		require("nvim-treesitter.configs").setup({
			ensure_installed = {
				"lua", "vim", "vimdoc", "bash", "json", "yaml", "markdown",
				"python", "c", "cpp", "javascript", "typescript", "vue",
			},
			-- meme bug pour markdown et bash : regression Neovim 0.12.x sur les predicats de
			-- requete treesitter, plante le highlighter (nvim/neovim#39032, nvim-treesitter#8618,
			-- nvim-treesitter#8636). Touche potentiellement d'autres langages -> si ca replante
			-- ailleurs, ajouter le langage ici. markdown_inline inclus (parser injecte separe).
			highlight = { enable = true, disable = { "markdown", "markdown_inline", "bash" } },
			indent = { enable = true },
		})

		-- filet de securite : force l'arret du highlighter treesitter sur ces filetypes, meme
		-- s'il a ete attache par un mecanisme independant de nvim-treesitter (ex: ftplugin natif)
		vim.api.nvim_create_autocmd("FileType", {
			pattern = { "markdown", "sh", "bash" },
			callback = function(args)
				vim.treesitter.stop(args.buf)
			end,
		})
	end,
}

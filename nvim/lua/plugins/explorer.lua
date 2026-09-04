return {
	"nvim-tree/nvim-tree.lua",
	dependencies = { "nvim-tree/nvim-web-devicons" },
	lazy = false, -- charge au demarrage pour s'ouvrir automatiquement (cf config ci-dessous)
	keys = {
		{ "<leader>e", "<cmd>NvimTreeToggle<CR>", desc = "Explorer" },
	},
	opts = {
		view = { width = 32 },
		renderer = { group_empty = true },
		filters = { dotfiles = false },
		git = { enable = true },
		-- ferme nvim si l'explorer est la derniere fenetre ouverte
		actions = { open_file = { quit_on_open = false } },
	},
	config = function(_, opts)
		require("nvim-tree").setup(opts)
		vim.cmd("NvimTreeOpen")
	end,
}

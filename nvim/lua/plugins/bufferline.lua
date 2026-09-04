return {
	{
		"akinsho/bufferline.nvim",
		version = "*",
		event = "VeryLazy",
		dependencies = { "nvim-tree/nvim-web-devicons" },
		keys = {
			{ "]b", "<cmd>BufferLineCycleNext<CR>", desc = "Onglet suivant" },
			{ "[b", "<cmd>BufferLineCyclePrev<CR>", desc = "Onglet precedent" },
			-- :bdelete perturbe le layout des fenetres avec nvim-tree ouvert (passe en plein
			-- ecran) -> :BufDel (nvim-bufdel) preserve le layout, cf plugins/bufdel.lua
			{ "<leader>bd", "<cmd>BufDel<CR>", desc = "Fermer l'onglet" },
		},
		opts = {
			options = {
				diagnostics = "nvim_lsp",
				offsets = { { filetype = "NvimTree", text = "Explorer" } },
				-- par defaut bufferline ferme via "bdelete! %d" (clic sur le x de l'onglet,
				-- clic droit) -> meme bug de layout avec nvim-tree que <leader>bd, on route
				-- aussi ca vers BufDel
				close_command = function(bufnum)
					vim.cmd("BufDel " .. bufnum)
				end,
				right_mouse_command = function(bufnum)
					vim.cmd("BufDel " .. bufnum)
				end,
			},
		},
	},
	{
		"ojroques/nvim-bufdel",
		-- charge sur la commande elle-meme (keymap, close_command du clic sur l'onglet) plutot que
		-- VeryLazy : garantit que :BufDel existe des le premier appel, quel que soit le timing
		cmd = { "BufDel", "BufDelAll", "BufDelOthers" },
		opts = {},
	},
}

return {
	"Mofiqul/vscode.nvim",
	lazy = false, -- charge au demarrage (c'est le colorscheme, pas une feature a declencher)
	priority = 1000,
	opts = {
		style = "dark", -- VS Code "Dark+" (theme sombre par defaut)
	},
	config = function(_, opts)
		require("vscode").setup(opts)
		vim.cmd.colorscheme("vscode")
	end,
}

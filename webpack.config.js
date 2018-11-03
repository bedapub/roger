module.exports = {
    entry: [
        './roger/web/js/views/index.js'
    ],
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: ['babel-loader']
            }
        ]
    },
    output: {
        path: __dirname + '/roger/web/static',
        filename: 'bundle.js',
        publicPath: '/static'
    },
    stats: {
        errorDetails: true
    },
    devServer: {
        historyApiFallback: true,
        contentBase: './roger/web/templates'
    }
};

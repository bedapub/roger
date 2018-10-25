module.exports = {
    entry: {
        index: './roger/web/js/views/index.jsx',
        study: './roger/web/js/views/study.jsx'
    },
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
        filename: '[name]-bundle.js',
        publicPath: '/static'
    }
};

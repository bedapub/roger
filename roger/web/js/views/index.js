import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Switch} from "react-router-dom";
import {createMuiTheme, MuiThemeProvider} from '@material-ui/core/styles';
import "isomorphic-fetch"
import 'typeface-roboto';

import {NotFound} from "Roger/views/not_found";
import {StudiesView} from "Roger/views/studies";
import {ToStudyRouter} from "Roger/views/study/router";
import ErrorBoundary from "Roger/components/error_boundary"

const theme = createMuiTheme({
    typography: {
        useNextVariants: true,
    },
});

const App = () => (
    <MuiThemeProvider theme={theme}>
        <ErrorBoundary>
            <Router>
                <div>
                    <Switch>
                        <Route exact path="/" component={StudiesView}/>
                        <Route exact path="/study" component={StudiesView}/>
                        <Route path="/study/:studyName" component={ToStudyRouter}/>
                        <Route component={NotFound}/>
                    </Switch>
                </div>
            </Router>
        </ErrorBoundary>
    </MuiThemeProvider>
);

ReactDOM.render(<App/>, document.getElementById('app'));

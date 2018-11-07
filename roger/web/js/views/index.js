import React from 'react';
import ReactDOM from 'react-dom';
import {BrowserRouter as Router, Route, Switch} from "react-router-dom";
import {createMuiTheme, MuiThemeProvider} from '@material-ui/core/styles';
import {NotFound} from "./not_found";
import {StudiesView} from "./studies";
import {SingleStudyView} from "./study";
import "isomorphic-fetch"
import 'typeface-roboto';

import ErrorBoundary from "../components/error_boundary"

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
                        <Route path="/study/:studyName" component={SingleStudyView}/>
                        <Route component={NotFound}/>
                    </Switch>
                </div>
            </Router>
        </ErrorBoundary>
    </MuiThemeProvider>
);

ReactDOM.render(<App/>, document.getElementById('app'));

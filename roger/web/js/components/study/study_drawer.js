import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import {withStyles} from '@material-ui/core/styles';
import Drawer from '@material-ui/core/Drawer';
import CssBaseline from '@material-ui/core/CssBaseline';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import List from '@material-ui/core/List';
import Typography from '@material-ui/core/Typography';
import Divider from '@material-ui/core/Divider';
import IconButton from '@material-ui/core/IconButton';
import MenuIcon from '@material-ui/icons/Menu';
import ChevronLeftIcon from '@material-ui/icons/ChevronLeft';
import ChevronRightIcon from '@material-ui/icons/ChevronRight';
import ListItem from '@material-ui/core/ListItem';
import ListItemText from '@material-ui/core/ListItemText';
import {Link} from "react-router-dom";

const drawerWidth = 240;

const styles = theme => ({
    root: {
        display: 'flex',
    },
    appBar: {
        transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
        }),
    },
    appBarShift: {
        width: `calc(100% - ${drawerWidth}px)`,
        marginLeft: drawerWidth,
        transition: theme.transitions.create(['margin', 'width'], {
            easing: theme.transitions.easing.easeOut,
            duration: theme.transitions.duration.enteringScreen,
        }),
    },
    menuButton: {
        marginLeft: 12,
        marginRight: 20,
    },
    hide: {
        display: 'none',
    },
    drawer: {
        width: drawerWidth,
        flexShrink: 0,
    },
    drawerPaper: {
        width: drawerWidth,
    },
    drawerHeader: {
        display: 'flex',
        alignItems: 'center',
        padding: '0 8px',
        ...theme.mixins.toolbar,
        justifyContent: 'flex-end',
    },
    content: {
        flexGrow: 1,
        padding: theme.spacing.unit * 3,
        transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.leavingScreen,
        }),
        marginLeft: -drawerWidth,
    },
    contentShift: {
        transition: theme.transitions.create('margin', {
            easing: theme.transitions.easing.easeOut,
            duration: theme.transitions.duration.enteringScreen,
        }),
        marginLeft: 0,
    },
    nestedLevel1: {
        paddingLeft: theme.spacing.unit * 6,
    },
    nestedLevel2: {
        paddingLeft: theme.spacing.unit * 8,
    },
    navActive: []
});

function ListItemLink(props) {
    const {className, primary, to} = props;
    return (
        <li>
            <ListItem className={className} button component={Link} to={to}>
                <ListItemText primary={primary}/>
            </ListItem>
        </li>
    );
}

ListItemLink.propTypes = {
    primary: PropTypes.node.isRequired,
    to: PropTypes.string.isRequired,
};

class StudyDrawer extends React.Component {
    constructor(props) {
        super(props);
        this.state = {open: true};

        this.handleDrawerOpen = this.handleDrawerOpen.bind(this);
        this.handleDrawerClose = this.handleDrawerClose.bind(this);
    };

    handleDrawerOpen() {
        this.setState({open: true});
    };

    handleDrawerClose() {
        this.setState({open: false});
    };

    render() {
        const {classes, theme, study, basePath} = this.props;
        const {open} = this.state;

        return (
            <div className={classes.root}>
                <CssBaseline/>
                <AppBar position="fixed"
                        className={classNames(classes.appBar, {
                            [classes.appBarShift]: open,
                        })}>
                    <Toolbar disableGutters={!open}>
                        <IconButton color="inherit"
                                    aria-label="Open drawer"
                                    onClick={this.handleDrawerOpen}
                                    className={classNames(classes.menuButton, open && classes.hide)}>
                            <MenuIcon/>
                        </IconButton>
                        <Typography variant="h6" color="inherit" noWrap>
                            Study: {study.Name}
                        </Typography>
                    </Toolbar>
                </AppBar>
                <Drawer className={classes.drawer}
                        variant="persistent"
                        anchor="left"
                        open={open}
                        classes={{
                            paper: classes.drawerPaper,
                        }}>
                    <div className={classes.drawerHeader}>
                        <Typography variant="h6" noWrap>
                            ROGER
                        </Typography>
                        <IconButton onClick={this.handleDrawerClose}>
                            {theme.direction === 'ltr' ? <ChevronLeftIcon/> : <ChevronRightIcon/>}
                        </IconButton>
                    </div>
                    <Divider/>
                    <List component="nav">
                        <ListItemLink button to={`${basePath}`} primary="Overview"/>
                        <ListItemLink button to={`${basePath}/expression`} primary="Gene Expression"/>
                    </List>
                    <Divider/>
                    <List component="nav">
                        {study.Design.map(design => (
                            <li key={design.Name}>
                                <ListItem button component={Link} to={`${basePath}/design/${design.Name}`}>
                                    <ListItemText primary={design.Name}/>
                                </ListItem>
                                <List>
                                    {design.Contrast.map(contrast => (
                                        <li key={contrast.Name}>
                                            <ListItem className={classes.nestedLevel1} button component={Link}
                                                      to={`${basePath}/design/${design.Name}/contrast/${contrast.Name}`}>
                                                <ListItemText primary={contrast.Name}/>
                                            </ListItem>
                                            <List>
                                                {contrast.DGEmodel.map(dgeResult => (
                                                    <li key={dgeResult.MethodName}>
                                                        <ListItem className={classes.nestedLevel2} button
                                                                  component={Link}
                                                                  to={`${basePath}/design/`
                                                                  + `${design.Name}/contrast/`
                                                                  + `${contrast.Name}/dge/${dgeResult.MethodName}`}>
                                                            <ListItemText primary={`DGE with ${dgeResult.MethodName}`}/>
                                                        </ListItem>
                                                    </li>
                                                ))}
                                                {contrast.GSEresult.map(gseResult => (
                                                    <li key={gseResult.GSEMethodName}>
                                                        <ListItem className={classes.nestedLevel2} button
                                                                  component={Link}
                                                                  to={`${basePath}/design/`
                                                                  + `${design.Name}/contrast/`
                                                                  + `${contrast.Name}/dge/${gseResult.DGEMethodName}`
                                                                  + `${contrast.Name}/gse/${gseResult.GSEMethodName}`}>
                                                            <ListItemText
                                                                primary={`GSE with ${gseResult.GSEMethodName} `
                                                                + `and ${gseResult.DGEMethodName}`}/>
                                                        </ListItem>
                                                    </li>
                                                ))}
                                            </List>
                                        </li>
                                    ))}
                                </List>
                            </li>
                        ))}
                    </List>
                </Drawer>
                <main
                    className={classNames(classes.content, {
                        [classes.contentShift]: open,
                    })}>
                    <div className={classes.drawerHeader}/>
                    {this.props.children}
                </main>
            </div>
        );
    }
}

StudyDrawer.propTypes = {
    classes: PropTypes.object.isRequired,
    theme: PropTypes.object.isRequired,
    study: PropTypes.object.isRequired,
    basePath: PropTypes.string.isRequired
};

export default withStyles(styles, {withTheme: true})(StudyDrawer);
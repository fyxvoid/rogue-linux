/* Rogue Linux dwm config */
#include <X11/XF86keysym.h>

static const unsigned int borderpx  = 2;
static const unsigned int snap      = 32;
static const int showbar            = 1;
static const int topbar             = 1;
static const char *fonts[]          = { "monospace:size=11" };
static const char dmenufont[]       = "monospace:size=11";

/* Rogue dark colour scheme */
static const char col_bg[]     = "#0d1117";
static const char col_bar[]    = "#161b22";
static const char col_border[] = "#30363d";
static const char col_fg[]     = "#c9d1d9";
static const char col_sel[]    = "#58a6ff";
static const char col_selbdr[] = "#58a6ff";

static const char *colors[][3] = {
    /*               fg          bg          border   */
    [SchemeNorm] = { col_fg,     col_bar,    col_border },
    [SchemeSel]  = { col_bg,     col_sel,    col_selbdr },
};

static const char *tags[] = { "1", "2", "3", "4", "5", "6", "7", "8", "9" };

static const Rule rules[] = {
    /* class      instance    title       tags mask  isfloating  monitor */
    { "Alacritty", NULL,      NULL,       0,         0,          -1 },
    { "st",        NULL,      NULL,       0,         0,          -1 },
    { "firefox",   NULL,      NULL,       1 << 1,    0,          -1 },
};

/* layout(s) */
static const float mfact     = 0.55;
static const int nmaster     = 1;
static const int resizehints = 0;
static const int lockfullscreen = 1;

static const Layout layouts[] = {
    { "[]=",  tile },
    { "><>",  NULL },
    { "[M]",  monocle },
};

#define MODKEY Mod4Mask
#define TAGKEYS(KEY,TAG) \
    { MODKEY,                       KEY, view,       {.ui = 1 << TAG} }, \
    { MODKEY|ControlMask,           KEY, toggleview, {.ui = 1 << TAG} }, \
    { MODKEY|ShiftMask,             KEY, tag,        {.ui = 1 << TAG} }, \
    { MODKEY|ControlMask|ShiftMask, KEY, toggletag,  {.ui = 1 << TAG} },

#define SHCMD(cmd) { .v = (const char*[]){ "/bin/sh", "-c", cmd, NULL } }

static char dmenumon[2] = "0";
static const char *dmenucmd[]  = { "dmenu_run", "-m", dmenumon, "-fn", dmenufont,
                                   "-nb", col_bar, "-nf", col_fg,
                                   "-sb", col_sel, "-sf", col_bg, NULL };
static const char *termcmd[]   = { "st", NULL };
static const char *alacritty[] = { "alacritty", NULL };
static const char *filecmd[]   = { "st", "-e", "lf", NULL };

static const Key keys[] = {
    { MODKEY,            XK_p,      spawn,          {.v = dmenucmd } },
    { MODKEY|ShiftMask,  XK_Return, spawn,          {.v = termcmd } },
    { MODKEY,            XK_Return, spawn,          {.v = alacritty } },
    { MODKEY,            XK_e,      spawn,          {.v = filecmd } },
    { MODKEY,            XK_b,      togglebar,      {0} },
    { MODKEY,            XK_j,      focusstack,     {.i = +1 } },
    { MODKEY,            XK_k,      focusstack,     {.i = -1 } },
    { MODKEY,            XK_i,      incnmaster,     {.i = +1 } },
    { MODKEY,            XK_d,      incnmaster,     {.i = -1 } },
    { MODKEY,            XK_h,      setmfact,       {.f = -0.05} },
    { MODKEY,            XK_l,      setmfact,       {.f = +0.05} },
    { MODKEY,            XK_space,  zoom,           {0} },
    { MODKEY,            XK_Tab,    view,           {0} },
    { MODKEY|ShiftMask,  XK_c,      killclient,     {0} },
    { MODKEY,            XK_t,      setlayout,      {.v = &layouts[0]} },
    { MODKEY,            XK_f,      setlayout,      {.v = &layouts[1]} },
    { MODKEY,            XK_m,      setlayout,      {.v = &layouts[2]} },
    { MODKEY|ShiftMask,  XK_space,  togglefloating, {0} },
    { MODKEY,            XK_0,      view,           {.ui = ~0 } },
    { MODKEY|ShiftMask,  XK_0,      tag,            {.ui = ~0 } },
    { MODKEY,            XK_comma,  focusmon,       {.i = -1 } },
    { MODKEY,            XK_period, focusmon,       {.i = +1 } },
    { MODKEY|ShiftMask,  XK_comma,  tagmon,         {.i = -1 } },
    { MODKEY|ShiftMask,  XK_period, tagmon,         {.i = +1 } },
    TAGKEYS(             XK_1,                      0)
    TAGKEYS(             XK_2,                      1)
    TAGKEYS(             XK_3,                      2)
    TAGKEYS(             XK_4,                      3)
    TAGKEYS(             XK_5,                      4)
    TAGKEYS(             XK_6,                      5)
    TAGKEYS(             XK_7,                      6)
    TAGKEYS(             XK_8,                      7)
    TAGKEYS(             XK_9,                      8)
    { MODKEY|ShiftMask,  XK_q,      quit,           {0} },
};

static const Button buttons[] = {
    { ClkTagBar,          0,         Button1, view,           {0} },
    { ClkTagBar,          0,         Button3, toggleview,     {0} },
    { ClkTagBar,          MODKEY,    Button1, tag,            {0} },
    { ClkTagBar,          MODKEY,    Button3, toggletag,      {0} },
    { ClkWinTitle,        0,         Button2, zoom,           {0} },
    { ClkStatusText,      0,         Button2, spawn,          {.v = termcmd } },
    { ClkClientWin,       MODKEY,    Button1, movemouse,      {0} },
    { ClkClientWin,       MODKEY,    Button2, togglefloating, {0} },
    { ClkClientWin,       MODKEY,    Button3, resizemouse,    {0} },
    { ClkRootWin,         0,         Button2, spawn,          {.v = termcmd } },
};

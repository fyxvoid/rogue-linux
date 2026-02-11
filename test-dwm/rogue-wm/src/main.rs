use penrose::{
    builtin::{
        actions::{exit, spawn, modify_with},
        layout::MainAndStack,
    },
    core::{
        bindings::parse_keybindings_with_xmodmap,
        layout::Layout,
        Config, WindowManager,
    },
    stack,
    x11rb::RustConn,
    Result,
};
use std::collections::HashMap;
use tracing_subscriber;

// Aesthetics: Cyberpunk / Rogue Linux Palette
const COLOR_BLUE: &str = "#00f3ff";
const COLOR_GRAY: &str = "#444444";

fn main() -> Result<()> {
    tracing_subscriber::fmt::init();

    // Layout configuration
    let layouts = stack!(
        Box::new(MainAndStack::side_unboxed(1, 0.6, 0.1, false)) as Box<dyn Layout>,
        Box::new(MainAndStack::bottom_unboxed(1, 0.6, 0.1, false)) as Box<dyn Layout>,
        penrose::builtin::layout::Monocle::boxed()
    );

    let config: Config<RustConn> = Config {
        normal_border: COLOR_GRAY.try_into().expect("valid color"),
        focused_border: COLOR_BLUE.try_into().expect("valid color"),
        default_layouts: layouts,
        ..Config::default()
    };

    let mut raw_bindings = HashMap::new();
    
    // Core Actions
    raw_bindings.insert("M-Return".to_string(), spawn("alacritty"));
    raw_bindings.insert("M-p".to_string(), spawn("dmenu_run"));
    raw_bindings.insert("M-S-q".to_string(), exit());
    
    // Custom Kill Action
    raw_bindings.insert("M-S-c".to_string(), modify_with(|cs| {
        if let Some(&id) = cs.current_client() {
            // In 0.3.6, the refresh will handle the unmapping if we remove it from state
            cs.remove_focused();
        }
    }));
    
    // Workspace Switching (1-9)
    for i in 1..10 {
        let tag = i.to_string();
        raw_bindings.insert(format!("M-{}", i), modify_with(move |cs| cs.focus_tag(&tag)));
        
        let tag_move = i.to_string();
        raw_bindings.insert(format!("M-S-{}", i), modify_with(move |cs| {
            if let Some(&id) = cs.current_client() {
                cs.move_client_to_tag(&id, &tag_move);
            }
        }));
    }

    // Tiling Logic
    raw_bindings.insert("M-j".to_string(), modify_with(|cs| cs.focus_down()));
    raw_bindings.insert("M-k".to_string(), modify_with(|cs| cs.focus_up()));
    raw_bindings.insert("M-S-j".to_string(), modify_with(|cs| cs.swap_down()));
    raw_bindings.insert("M-S-k".to_string(), modify_with(|cs| cs.swap_up()));
    raw_bindings.insert("M-space".to_string(), modify_with(|cs| cs.next_layout()));

    let key_bindings = parse_keybindings_with_xmodmap(raw_bindings)?;
    let conn = RustConn::new()?;
    
    // WindowManager::new(config, keybindings, mousebindings, xconn)
    let mut wm = WindowManager::new(config, key_bindings, HashMap::new(), conn)?;

    wm.run()
}

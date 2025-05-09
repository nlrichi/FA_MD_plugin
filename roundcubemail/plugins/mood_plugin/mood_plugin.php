<?php

class mood_plugin extends rcube_plugin
{
    public $task = 'mail';

    function init()
    {
        $rcube = rcmail::get_instance();
        
        if ($rcube->action == 'compose') {
            $this->add_hook('render_page', array($this, 'add_mood_button'));
            $this->include_script('mood_plugin.js');
            $this->include_stylesheet('mood_plugin.css');
        }
    }

    function add_mood_button($args)
    {
        if ($args['template'] == 'compose') {
            
            error_log("add_mood_button called");
            $args['content'] .= html::tag('li', null, 
                $this->api->output->button(array(
                    'command' => 'detect-mood',
                    'id' => 'mood-btn',
                    'type' => 'button',
                    'class' => 'button mood-button',
                    'label' => 'Detect Mood',
                    'title' => 'Detect your mood'
                ))
            );
            
            return $args;
        }
    }
}
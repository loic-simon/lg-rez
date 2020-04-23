import traceback

class ChatfuelBase(dict):
    """Base of all Chatfuel objects.
    
    Based on https://docs.chatfuel.com/en/articles/735122-json-api"""
    
    def __init__(self):
        dict.__init__(self)
        self.contents = "None"
    
    def __repr__(self):
        return f"<Chatfuel{type(self).__name__}: {repr(self.contents)}>"


class Response(ChatfuelBase):
    """Dict: a response to use Chatfuel interactively
    
    Syntax: Response(Messages, set_attributes=None, redirect_to_blocks=None)
    Messages must be a list/tuple/... of Chatfuel messages (instances of ChatfuelMessage)
    
    The optionnal argument "set_attributes" can be used to set user attributes. Syntax: dict {attibute1:value1, attibute2:value2...}
    The optionnal argument "redirect_to_blocks" can be used to redirect users after all Messages. Must be either an exising block name or a list of exising blocks, using their names as defined in Chatfuel (not block ID!)"""
    
    def __init__(self, Messages, set_attributes=None, redirect_to_blocks=None):
        ChatfuelBase.__init__(self)
        
        try:
            for m in Messages:
                if not isinstance(m, ChatfuelMessage):
                    raise TypeError(f"All elements of LQR must be instances of ChatfuelMessage. Received: {type(m)}")
        except TypeError:
            raise TypeError("Argument of Response must be a subscriptable of instances of ChatfuelMessage.")
        
        self["messages"] = list(Messages)
        self.contents = list(Messages)
        
        if set_attributes != None:
            if isinstance(set_attributes, dict):
                self["set_attributes"] = set_attributes
                self.contents += f"(set_attributes:{set_attributes.keys()})"
            else:
                raise TypeError("Optionnal argument set_attributes must be an instance of dict")
        
        if redirect_to_blocks != None:
            if isinstance(redirect_to_blocks, str):
                self["redirect_to_blocks"] = [redirect_to_blocks]
            else:
                self["redirect_to_blocks"] = redirect_to_blocks
            self.contents += f"(redirect_to:{set_attributes.keys()})"


class ErrorReport(Response):
    """Call in place of Response for reporting any Python error to the Chatfuel end user.
    
    Syntax: ErrorReport(exception, verbose=False, message="WARNING - PYTHON ERROR:")"""
    
    def __init__(self, exc, verbose=False, message="WARNING - PYTHON ERROR:"):
        m1 = Text(message)
        if verbose:
            m2 = Text(traceback.format_exc())
        else:
            m2 = Text(f"{type(exc).__name__} : {exc}")
        Response.__init__(self, [m1, m2])


class Button(ChatfuelBase):
    """A button. To be used in Buttons message or .addQuickReplies message method.
    
    Syntax: Button(button type (str), button title (str), button action (str, dependent on the Button type), set_attributes=None)
    
    Possible button types:
        - "show_block": redirect user to one (str) of more (list of str) exising blocks, using their names as defined in Chatfuel (not block ID!)
        - "web_url": redirect user to any external URL.
        - "json_plugin_url": redirect user to any other backend API apeg
        - "phone_number"
        
    For types "show_block", "json_plugin_url" and "" (no action), the optionnal argument "set_attributes" can be used to set user attributes. Syntax: dict {attibute1:value1, attibute2:value2...}"""

    BUTTON_TYPES = ["show_block",
                    "web_url",
                    "json_plugin_url",
                    "phone_number",
                    ""]
                    
    def __init__(self, btype, btitle, bact, set_attributes=None):
        ChatfuelBase.__init__(self)
        if btype in self.BUTTON_TYPES:
            self["title"] = btitle
            self["type"] = btype
            if btype == "show_block":       # Redirect to one or several block(s)
                if isinstance(bact, str):
                    self["block_names"] = [bact]
                else:
                    self["block_names"] = bact
            elif btype == "phone_number":   # Special phone aspect
                self["phone_number"] = bact
            elif btype.endswith("url"):
                self["url"] = bact
            self.contents = f"{btitle} ({btype}:{bact})"
            
            if btype in ["show_block", "json_plugin_url", ""] and set_attributes:
                if isinstance(set_attributes, dict):
                    self["set_attributes"] = set_attributes
                    self.contents += f"(set_attributes:{set_attributes.keys()})"
                else:
                    raise TypeError("Optionnal argument set_attributes must be an instance of dict")
        else:
            raise TypeError("Unknow button type. See Button.BUTTON_TYPES for allowed types.")
        

class ChatfuelMessage(ChatfuelBase):
    """Base of all Chatfuel messages. To be integrated in a Response."""
    
    def addQuickReplies(self, LQR, process_text_by_ai=True, save_to_attribute=None):
        """Use this method to add quick replies (instances of Button) to your Message. 
        
        LQR must be a non-empty subscriptable of Button objets. Messenger is limited to 11 replies per Message.
        
        You might want to use additional arguments:
            - "process_text_by_ai": Specifies how to handle user input sent after the Quick Reply. If False, user will be sent to the next card, instead of AI recognition (default).
            - "save_to_attribute": If specified, user input sent after the Quick Reply will be saved into the specified user attribute."""
            
        try:
            if len(LQR) < 1 or len(LQR) > 11:
                raise ValueError(f"min 1 to max 11 quick replies per addQuickReplies block required. Received: {len(LQR)}")
            else:
                for QR in LQR:
                    if not isinstance(QR, Button):
                        raise TypeError(f"All elements of LQR must be instances of Button. Received: {type(QR)}")
        except TypeError:
            raise TypeError("addQuickReplies argument must be a non-empty subscriptable of Button objets.")
                        
        self["quick_replies"] = list(LQR)
        self.contents += f" + {list(LQR)}"
            
        if (not process_text_by_ai) or (save_to_attribute != None):     # Options
            self["quick_reply_options"] = {}
            if not process_text_by_ai:
                self["quick_reply_options"]["process_text_by_ai"] = False
                self.contents += "(NO AI)"
            if save_to_attribute != None:
                self["quick_reply_options"]["text_attribute_name"] = save_to_attribute        
                self.contents += f"(SAVE TO {save_to_attribute})"
                
        return self
    
    # def fget(self): return self[self.principal]
    # def fset(self, v): self[self.principal] = v
    # contents = property(fget, fset)
        

class Text(ChatfuelMessage):
    """Use this response to send text messages.
    
    Syntax: Text(str text)"""
    
    def __init__(self, text):
        ChatfuelBase.__init__(self)
        self.contents = text
        self["text"] = self.contents
        

class Image(ChatfuelMessage):
    """Use this response to send image files. 
    
    Messenger supports JPG, PNG and GIF images. If you are having issues with GIF rendering, please try to reduce the file size.
    Syntax: Text(image url (str))"""
    
    def __init__(self, url):
        ChatfuelBase.__init__(self)
        self.contents = url
        self["attachment"] = {"type": "image", 
                              "payload": {
                                "url": self.contents
                              }}


class Video(ChatfuelMessage):
    """Use this response to send video files. 
    
    Messenger supports MP4 videos, which are up to 25MB in size.
    Syntax: Text(video url (str))"""
    
    def __init__(self, url):
        ChatfuelBase.__init__(self)
        self.contents = url
        self["attachment"] = {"type": "video", 
                              "payload": {
                                "url": self.contents
                              }}


class Audio(ChatfuelMessage):
    """Use this response to send audio files. 
    
    Messenger supports MP3, OGG, WAV audios, which are up to 25MB in size.
    Syntax: Text(audio file url (str))"""
    
    def __init__(self, url):
        ChatfuelBase.__init__(self)
        self.contents = url
        self["attachment"] = {"type": "audio", 
                              "payload": {
                                "url": self.contents
                              }}


class File(ChatfuelMessage):
    """Use this response to send any other files, which are no larger than 25 MB.
    Syntax: Text(file url (str))"""
    
    def __init__(self, url):
        ChatfuelBase.__init__(self)
        self.contents = url
        self["attachment"] = {"type": "file", 
                              "payload": {
                                "url": self.contents
                              }}


class Buttons(ChatfuelMessage):
    """Use this class to add buttons to your responses. 
    
    You can set buttons to link to a block in the dashboard, open a website, or send another request to your backend. 
    Buttons are limited to 3 items per message (= max 3 <Button> in a <Buttons>).
    
    Syntax: Button(button text, LB)
    LB must be a non-empty subscriptable of Button objets. Messenger is limited to 3 buttons per Message."""

    
    def __init__(self, text, LB):
        ChatfuelBase.__init__(self)
        try:
            if len(LB) < 1 or len(LB) > 3:
                raise ValueError(f"min 1 to max 3 buttons per Buttons block required. Received: {len(LB)}")
            else:
                for b in LB:
                    if not isinstance(b, Button):
                        raise TypeError(f"All elements of LB must be instances of Button. Received: {type(b)}")
        except TypeError:
            raise TypeError("2nd argument of Buttons must be a non-empty subscriptable of Button objets")
            
        self["attachment"] = {"type": "template", 
                              "payload": {
                                "text": text,
                                "template_type": "button",
                                "buttons": list(LB)
                              }}
        self.contents = f"{text} >{list(LB)}"



        












class QuickReply(ChatfuelBase):
    """Depreciated. Use Button instead."""
    
    QR_TYPES = ["show_block",
                "set_attributes",
                "web_url",
                "json_plugin_url"]
                    
    def __init__(self, QRtype, QRtitle, QRarg):
        ChatfuelBase.__init__(self)
        if QRtype in self.QR_TYPES:
            self["title"] = QRtitle
            if QRtype == "show_block":
                self["block_names"] = [QRarg]
            elif QRtype == "phone_number":
                self["phone_number"] = QRarg
            else:
                self["type"] = QRtype
                self["url"] = QRarg
            self.contents = f"{QRtitle} ({QRtype}:{QRarg})"
        else:
            raise TypeError("Unknow quick reply type. See QuickReply.QR_TYPES for allowed types.")


        

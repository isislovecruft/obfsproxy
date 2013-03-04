import collections
import logging
import pits

class Transcript(object):
    """
    Manages the PITS transcript. Also contains the functions that
    verify the transcript against the test case file.

    Attributes:
    'text', the transcript text.
    """

    def __init__(self):
        self.text = ''

    def write(self, data):
        """Write 'data' to transcript."""

        self.text += data
        self.text += '\n'

    def get(self):
        return self.text

    def test_was_success(self, original_script):
        """
        Validate transcript against test case file. Return True if the
        test was successful and False otherwise.
        """
        postprocessed_script = self._postprocess(original_script)
        postprocessed_transcript = self._postprocess(self.text)

        # Log the results
        log_func = logging.debug if postprocessed_script == postprocessed_transcript else logging.warning
        log_func("postprocessed_script:\n'%s'" % postprocessed_script)
        log_func("postprocessed_transcript:\n'%s'" % postprocessed_transcript)

        return postprocessed_script == postprocessed_transcript

    def _postprocess(self, script):
        """
        Post-process a (trans)script, according to the instructions of
        the "Test case results" section.

        Return the postprocessed string.

        Assume correctly formatted script file.
        """
        logging.debug("Postprocessing:\n%s" % script)

        postprocessed = ''
        outbound_events = [] # Events of the outbound connections
        inbound_events = [] # Events of the inbound connections
        # Data towards outbound connections (<identifier> -> <outbound data>)
        outbound_data = collections.OrderedDict()
        # Data towards inbound connections (<identifier> -> <inbound data>)
        inbound_data = collections.OrderedDict()

        for line in script.split('\n'):
            line = line.rstrip()
            if line == '':
                continue

            tokens = line.split(" ")

            if tokens[0] == 'P' or tokens[0] == '#': # Ignore
                continue
            elif tokens[0] == '!': # Count '!' as inbound event
                inbound_events.append(line)
            elif tokens[0] == '*': # Count '*' as outbound event
                outbound_events.append(line)
            elif tokens[0] == '>': # Data towards inbound socket
                if not tokens[1] in inbound_data:
                    inbound_data[tokens[1]] = ''

                inbound_data[tokens[1]] += ' '.join(tokens[2:])
            elif tokens[0] == '<': # Data towards outbound socket
                if not tokens[1] in outbound_data:
                    outbound_data[tokens[1]] = ''

                outbound_data[tokens[1]] += ' '.join(tokens[2:])

        """
        Inbound-related events and traffic go on top, the rest go to
        the bottom. Event lines go on top, transmit lines on bottom.
        """

        # Inbound lines
        postprocessed += '\n'.join(inbound_events)
        postprocessed += '\n'
        for identifier, data in inbound_data.items():
            postprocessed += '> %s %s\n' % (identifier, data)

        # Outbound lines
        postprocessed += '\n'.join(outbound_events)
        for identifier, data in outbound_data.items():
            postprocessed += '< %s %s\n' % (identifier, data)

        return postprocessed

class LoadPrompt:
    @staticmethod
    def load_prompt(prompt_file):
        with open(prompt_file, 'r') as f:
            prompt = f.read()
        return prompt
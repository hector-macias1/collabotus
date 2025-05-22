class LoadPrompt:
    @staticmethod
    def load_prompt(prompt_file):
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read()
        return prompt
import os
from pathlib import Path
from typing import Dict, List, Optional

import ruamel.yaml


class PreCommitConfigManager:
    def __init__(self, path: str):
        self.path = Path(path).resolve()
        self.yaml = ruamel.yaml.YAML()
        self.yaml.preserve_quotes = True

    def path_exists(self) -> bool:
        """Check if path exists."""
        return self.path.exists()

    def is_git_root(self) -> bool:
        """Check if path is root of git."""
        return (self.path / '.git').exists()

    def config_exists(self) -> bool:
        """Check if .pre-commit-config.yaml exists."""
        return (self.path / '.pre-commit-config.yaml').exists()

    def is_config_empty(self) -> bool:
        """Check if .pre-commit-config.yaml is empty."""
        config_file = self.path / '.pre-commit-config.yaml'
        return config_file.stat().st_size == 0 if config_file.exists() else False

    def _load_config(self) -> Optional[dict]:
        config_file = self.path / '.pre-commit-config.yaml'

        if not config_file.exists():
            return {'repos': []}
        try:
            with open(config_file, 'r') as f:
                content = self.yaml.load(f) or {'repos': []}
            content.setdefault('repos', [])
            return content
        except Exception as e:
            raise RuntimeError(f'Failed to load config: {str(e)}')

    def get_missing_rules(self, required_rules: List[Dict]) -> List[Dict]:
        """获取缺失的规则."""
        current_config = self._load_config()
        existing_repos = {r['repo']: r for r in current_config['repos']}

        missing = []
        for rule in required_rules:
            repo_url = rule.get('repo', '')
            if repo_url not in existing_repos:
                missing.append(rule)
            else:
                # 检查hook是否完整（可选增强）
                pass
        return missing

    def write_rules(self, missing_rules: List[Dict]) -> None:
        """写入缺失规则到配置文件."""
        config_file = self.path / '.pre-commit-config.yaml'
        config = self._load_config()

        # 添加缺失规则
        for rule in missing_rules:
            config['repos'].append(ruamel.yaml.comments.CommentedMap(rule))

        # 确保目录存在
        config_file.parent.mkdir(parents=True, exist_ok=True)

        with open(config_file, 'w') as f:
            self.yaml.dump(config, f)


def main():
    parser = argparse.ArgumentParser(
        description='configure .pre-commit-config.yaml automaticlly', formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--path', type=str, default='./', help='Specify a Git repository root directory path')
    parser.add_argument(
        '--type',
        type=str,
        default='python',
        help='Specify the primary language of the project;Now only support python.',
    )
    parser.add_argument('--check', action='store_true', help='check local .pre-commit-config.yaml missing rules')
    args = parser.parse_args()

    try:
        with open(args.rules, 'r') as f:
            required_rules = json.load(f)

        manager = PreCommitConfigManager(args.path)
        if not manager.path_exists() or not manager.is_git_root():
            sys.exit('path is not exists or not a git repository ')

        full_rules = None
        if args.type == 'python':
            with open('python/pre-commit-config.yaml', 'r') as f:
                full_rules = json.load(f)
        else:
            sys.exit(f"Now don't support {args.type}")

        if not manager.config_exists():
            with open(f'{args.path}/.pre-commit-config.yaml', 'w') as f:
                manager.yaml.dump(full_rules, f)
        else:
            print('There exists origin .pre-commit-config.yaml')

        if args.check:
            print('Only check missing rules')
    except Exception as e:
        sys.exit(f'Error:{str(e)}')


if __name__ == '__main__':
    main()

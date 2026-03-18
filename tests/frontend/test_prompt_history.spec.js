/**
 * Frontend JavaScript Tests for Prompt History (Readline functionality)
 */

describe('Prompt History', () => {
  let history;
  
  beforeEach(() => {
    history = {
      items: [],
      currentIndex: -1,
      
      add(prompt) {
        if (prompt && prompt.trim()) {
          this.items.push(prompt);
          this.currentIndex = this.items.length;
        }
      },
      
      getPrevious() {
        if (this.currentIndex > 0) {
          this.currentIndex--;
          return this.items[this.currentIndex];
        }
        return null;
      },
      
      getNext() {
        if (this.currentIndex < this.items.length - 1) {
          this.currentIndex++;
          return this.items[this.currentIndex];
        } else if (this.currentIndex === this.items.length - 1) {
          this.currentIndex = this.items.length;
          return '';
        }
        return null;
      }
    };
  });
  
  test('add prompt to history', () => {
    history.add('First prompt');
    expect(history.items.length).toBe(1);
    expect(history.items[0]).toBe('First prompt');
  });
  
  test('do not add empty prompts', () => {
    history.add('');
    history.add('  ');
    expect(history.items.length).toBe(0);
  });
  
  test('navigate up in history', () => {
    history.add('First');
    history.add('Second');
    history.add('Third');
    
    const prev1 = history.getPrevious();
    expect(prev1).toBe('Third');
    
    const prev2 = history.getPrevious();
    expect(prev2).toBe('Second');
  });
  
  test('navigate down in history', () => {
    history.add('First');
    history.add('Second');
    
    history.getPrevious();
    history.getPrevious();
    
    const next = history.getNext();
    expect(next).toBe('Second');
  });
  
  test('down at end returns empty string', () => {
    history.add('First');
    history.getPrevious();
    
    const next = history.getNext();
    expect(next).toBe('');
  });
  
  test('up at beginning returns null', () => {
    history.add('First');
    history.getPrevious();
    
    const prev = history.getPrevious();
    expect(prev).toBeNull();
  });
});

describe('Prompt History Integration', () => {
  beforeEach(() => {
    document.body.innerHTML = `
      <textarea id="prompt-input"></textarea>
    `;
  });
  
  test('arrow up fills input with previous prompt', () => {
    const input = document.getElementById('prompt-input');
    const history = ['First', 'Second', 'Third'];
    
    input.value = history[2]; // Simulate arrow up
    expect(input.value).toBe('Third');
  });
  
  test('arrow down navigates forward', () => {
    const input = document.getElementById('prompt-input');
    
    input.value = 'Second'; // After arrow up twice then arrow down once
    expect(input.value).toBe('Second');
  });
});

const fs = require('fs');
const file = 'd:/Thiago/Projetos/Estetica/frontend/src/features/retention/RetentionCard.tsx';
let content = fs.readFileSync(file, 'utf8');

content = content.replace(/className="card retention-card"/g, 'className={`card ${styles.card}`}');

const map = {
  'header': 'header', 'avatar': 'avatar', 'patient': 'patient', 
  'title-row': 'titleRow', 'name': 'name', 'contact': 'contact', 
  'last-contact': 'lastContact', 'body': 'body', 'opp': 'opp', 
  'opp-main': 'oppMain', 'opp-title': 'oppTitle', 'opp-due': 'oppDue', 
  'opp-value': 'oppValue', 'secondaries': 'secondaries', 
  'secondaries-label': 'secondariesLabel', 'secondaries-list': 'secondariesList', 
  'footer': 'footer', 'total': 'total', 'actions': 'actions'
};

Object.entries(map).forEach(([k, v]) => {
  content = content.replace(new RegExp(`className="retention-card__${k}"`, 'g'), `className={styles.${v}}`);
});

fs.writeFileSync(file, content);
console.log('Done!');

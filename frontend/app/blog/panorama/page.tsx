import { redirect } from 'next/navigation';

// SEO-460: /blog/panorama sem slug → redireciona para hub do blog.
// A rota real é /blog/panorama/[setor]. Esta página evita 404 quando
// o Google crawla o hub sem slug (descoberto via links internos).
export default function BlogPanoramaHubPage() {
  redirect('/blog');
}
